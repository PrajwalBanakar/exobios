-- Adds content-hash-based idempotency support to public.documents.
--
-- Context: document_id used to be a random uuid4 generated fresh on every
-- ingestion run (see ingestion/loaders/loader.py), so re-ingesting the same
-- file — after a crash, a retry, or just running the pipeline twice — wrote
-- a second, distinct row here and a second, distinct set of vectors into
-- Qdrant. document_id is now derived deterministically from a SHA-256 of the
-- source file's bytes, and services/upload.py::save_document_metadata now
-- upserts on document_id instead of inserting, so re-ingesting identical
-- content is a no-op update rather than a duplicate. content_hash is stored
-- so that fact is inspectable without recomputing it, and updated_at makes
-- "this document was re-ingested" visible.
--
-- Safe to re-run (idempotent) thanks to IF NOT EXISTS / OR REPLACE.

alter table public.documents
    add column if not exists content_hash text;

alter table public.documents
    add column if not exists updated_at timestamptz not null default now();

comment on column public.documents.content_hash is
    'SHA-256 hex digest of the source file bytes at ingestion time. document_id is derived from this, so identical content always maps to the same row.';
comment on column public.documents.updated_at is
    'Set on every insert/upsert. A value newer than created_at means this document was re-ingested (content_hash may be unchanged if it was just a re-run).';

-- Keep updated_at current on every upsert without relying on the client to set it.
create or replace function public.set_documents_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists documents_set_updated_at on public.documents;
create trigger documents_set_updated_at
    before insert or update on public.documents
    for each row execute function public.set_documents_updated_at();
