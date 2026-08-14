-- Adds the SAFE FOUNDATION for document versioning/supersession to
-- public.documents. Deliberately does not delete or touch any existing
-- Qdrant vectors — see the 2026-08 audit's Priority 8 for the full
-- rationale and what is intentionally NOT built here.
--
-- Problem this addresses: document_id is content-hash-derived (see the
-- 20260814000000 migration), so re-ingesting a MODIFIED file produces a
-- brand-new document_id/row/set of Qdrant vectors — the OLD version's
-- vectors are never deleted (correct — see "Do NOT automatically delete
-- historical vectors" in the audit) but were, before this migration, also
-- never marked as superseded. Retrieval had no way to prefer the current
-- version over a stale one for the same logical document; both were
-- equally "active" and both would compete in Qdrant search results.
--
-- What this migration adds:
--   logical_document_key  — groups document_id rows that represent
--                            different versions of "the same" document.
--                            Populated as the source filename's stem by
--                            ingestion/loaders/loader.py — a reasonable,
--                            documented DEFAULT heuristic, not a hard
--                            product decision. If documents are ever
--                            renamed between versions, or two unrelated
--                            documents share a filename, this heuristic
--                            will get it wrong; replacing it with an
--                            explicit, operator-supplied logical id is a
--                            product decision this migration does not make.
--   is_active              — true for the current/approved version of a
--                            logical document, false for a superseded one.
--                            Defaults true (every existing row is treated
--                            as active, since nothing before this migration
--                            tracked supersession at all).
--   superseded_by          — the document_id of the version that replaced
--                            this row, when is_active = false.
--
-- app/services/qdrant_service.py's hybrid_search now excludes chunks whose
-- document_payload.is_active is explicitly false — but a chunk with NO
-- is_active field at all (the entire pre-this-change corpus) still
-- matches, so this is non-destructive and requires no re-ingestion to take
-- effect for existing data.

alter table public.documents
    add column if not exists logical_document_key text;

alter table public.documents
    add column if not exists is_active boolean not null default true;

alter table public.documents
    add column if not exists superseded_by uuid references public.documents(document_id);

comment on column public.documents.logical_document_key is
    'Groups document_id rows representing different versions of the same logical document. Currently populated as the source filename stem by loaders/loader.py — a default heuristic, not a permanent product decision.';
comment on column public.documents.is_active is
    'False once a newer version (see superseded_by) of the same logical_document_key has completed ingestion. Retrieval (app/services/qdrant_service.py) excludes chunks explicitly marked inactive.';
comment on column public.documents.superseded_by is
    'The document_id of the version that superseded this row. Set only alongside is_active=false.';

create index if not exists documents_logical_document_key_idx on public.documents (logical_document_key);
create index if not exists documents_is_active_idx on public.documents (is_active);
