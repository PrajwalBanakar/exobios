-- Exobios AI ingestion pipeline — Supabase schema.
--
-- Derived EXACTLY from the only Supabase call in the codebase:
--   ingestion/services/upload.py::save_document_metadata()
--     supabase_client.table("documents").insert(metadata.model_dump()).execute()
-- where `metadata` is ingestion/schemas/document_schema.py::DocumentMetadata:
--     document_id: str          (a str(uuid.uuid4()) generated per ingested file,
--                                 see ingestion/loaders/loader.py::run())
--     document_title: str
--     complaint_category: str
--     applicable_roles: List[str]
--     file_location: str
--
-- No other table, RPC, view, or Supabase Storage call exists anywhere in
-- ingestion/ (verified via grep across the whole project) — this is the only
-- table required for the ingestion pipeline to run end to end. No SELECT,
-- UPDATE, or DELETE is issued against it anywhere either (insert-only), so
-- no query-driven indexes are added here beyond the implicit primary key
-- index — add them if/when a read path is introduced.
--
-- Run this once, in full, in the Supabase SQL Editor for your project
-- (Project -> SQL Editor -> New query -> paste -> Run). Safe to re-run
-- (idempotent) thanks to IF NOT EXISTS.

create table if not exists public.documents (
    document_id       uuid primary key,
    document_title    text not null,
    complaint_category text not null,
    applicable_roles  text[] not null default '{}',
    file_location     text not null,
    -- Not sent by the current insert (model_dump() only includes the 5
    -- fields above) — this is standard auditability, added by us, not
    -- required by the app code. Populated automatically by the DB default.
    created_at        timestamptz not null default now()
);

comment on table public.documents is
    'Document metadata written by ingestion/services/upload.py::save_document_metadata(). One row per ingested source document (PDF). Full text + vectors live in Qdrant; this table is metadata only.';

-- Row Level Security: enabled with NO policies. This is Supabase's own
-- recommended safe default — it blocks all access via the publishable
-- (anon) key. The ingestion pipeline must use a SECRET key
-- (sb_secret_...), which carries BYPASSRLS and is unaffected by RLS being
-- on or by the absence of policies. Do not add a permissive policy here
-- unless you specifically need the publishable/anon key to read this table
-- from a client app — nothing in the current codebase does.
alter table public.documents enable row level security;

-- Table-level grants: Postgres does not automatically give service_role
-- privileges on a newly created table (RLS and GRANTs are separate layers —
-- bypassing RLS does not bypass a missing GRANT). The ingestion pipeline
-- authenticates as service_role via the secret key, so it needs this
-- explicit grant or every insert fails with `permission denied for table
-- documents` (42501), independent of the RLS policy above.
grant usage on schema public to service_role;
grant select, insert, update, delete on public.documents to service_role;
