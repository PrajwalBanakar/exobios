-- Adds an explicit ingestion status lifecycle to public.documents.
--
-- Context: idempotency (previous migration, 20260814000000) means
-- re-running ingestion on the same file no longer duplicates data, but a
-- document could still end up "complete-looking" in Supabase (a row exists)
-- while actually having zero vectors in Qdrant, if chunking/embedding/the
-- Qdrant upsert failed after the metadata row was written — with no way to
-- tell that apart from a genuinely fully-ingested document. status makes
-- that distinction explicit: a document is only COMPLETED once parsing,
-- chunking, embedding, and the Qdrant upsert have all actually succeeded
-- (see ingestion/loaders/loader.py::run()). error_message carries a short,
-- truncated (max 500 chars in application code — see
-- services/upload.py::update_document_status), non-secret failure reason
-- for FAILED rows, not a full stack trace.
--
-- Safe to re-run (idempotent) thanks to IF NOT EXISTS / OR REPLACE and a
-- guarded constraint-add. Existing rows (all pre-dating this column) get
-- the DEFAULT 'PENDING' — technically inaccurate for rows that already
-- completed successfully before this migration, but harmless: nothing
-- currently reads this column to gate behavior, and a one-time backfill to
-- 'COMPLETED' for pre-existing rows is a manual follow-up, not something to
-- guess at here (we cannot know from this migration alone which pre-existing
-- rows actually have complete Qdrant vectors and which don't — that is
-- exactly the ambiguity this column exists to prevent going forward).

alter table public.documents
    add column if not exists status text not null default 'PENDING';

alter table public.documents
    add column if not exists error_message text;

do $$
begin
    if not exists (
        select 1 from pg_constraint where conname = 'documents_status_check'
    ) then
        alter table public.documents
            add constraint documents_status_check
            check (status in ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'));
    end if;
end $$;

comment on column public.documents.status is
    'PENDING (row exists, not yet processed) -> PROCESSING (metadata written, pipeline running) -> COMPLETED (chunked+embedded+Qdrant upsert all succeeded) or FAILED. Set by ingestion/loaders/loader.py::run() via services/upload.py::update_document_status().';
comment on column public.documents.error_message is
    'Short (<=500 char), truncated, non-secret failure reason for FAILED rows. Not a stack trace — see the full traceback in ingestion.log via the logger.exception call at the same site.';

-- Lets an operator/monitoring query cheaply find stuck-in-PROCESSING or
-- FAILED documents without a full table scan.
create index if not exists documents_status_idx on public.documents (status);
