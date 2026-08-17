# exobios-ai

RAG-based clinical decision support service for exobios. Two independent
projects, one shared Qdrant corpus.

> **New here?** Start with [`docs/LOCAL_SETUP.md`](docs/LOCAL_SETUP.md) for a
> from-scratch Windows setup, [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
> for how the pipeline works, and [`docs/POSTMAN_GUIDE.md`](docs/POSTMAN_GUIDE.md)
> to test the running service.

- **`ingestion/`** — offline batch pipeline. Parses client documents, chunks,
  classifies, embeds (dense + BM25 sparse), uploads raw/parsed files to S3,
  writes document metadata to Supabase, writes vectors + payload to Qdrant.
- **`app/`** — FastAPI service. Exposes `POST /analyze`, called by the Spring
  Boot backend. Runs a 4-stage LangGraph pipeline (diagnosis → investigation
  → treatment protocol → plan of action) against the Qdrant corpus, generates
  with an LLM, persists the running assessment state to MongoDB.

They share nothing at runtime except the Qdrant collection — `ingestion`
writes to it, `app` reads from it. Separate `.venv`s, separate `pyproject.toml`s.

---

## Current local status (verified, 2026-08-10)

- `app/` runs and passes a full live `/analyze` round trip: rule_engine ->
  Groq LLM calls -> Qdrant hybrid search -> MongoDB persistence, all real,
  no mocks.
- `ingestion/` has completed one real end-to-end run: `Biochemistry.pdf`
  (800 pages) -> 2,853 chunks -> embedded -> stored in Qdrant, with metadata
  written to Supabase. Collection `corpus` currently holds only this one
  document, which is a general biochemistry textbook, **not** a clinical
  diagnostic guideline — so `/analyze` correctly returns
  `insufficient_evidence: true` for symptom-based queries right now. That's
  the grounding safeguard working as intended, not a bug. Ingest an actual
  clinical reference (e.g. the IMNCI chart booklet already in this repo) to
  see real diagnosis candidates.
- **Known non-blocking issue**: the reranker's configured model
  (`cross-encoder/ms-marco-MiniLM-L-6-v2`) is no longer served by Hugging
  Face's `hf-inference` provider (`"error":"Model not supported by provider
  hf-inference"`, HTTP 400). `services/reranker_service.py`'s built-in
  fallback handles this correctly — retrieval still works, just falls back
  to unranked hybrid-search order. Needs a replacement model or provider,
  not urgent.
- Two real bugs found and fixed during the first ingestion run (see
  `git log` on `ingestion/chunkers/chunker.py` and
  `ingestion/embedder/embedder.py`): a debug `print()` loop that crashed on
  non-cp1252 Unicode in OCR'd text, and no retry/validation across ~2,850
  sequential embedding calls (one transient HF 500 used to abort the whole
  document).

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker (for local Qdrant)
- Accounts / credentials for: Hugging Face, Groq (LLM provider — note: Groq,
  not Grok/xAI). MongoDB and Qdrant run locally via Docker for development
  (see `docker-compose.yml`). AWS S3 and Supabase are only needed for the
  `ingestion/` pipeline, and S3 upload is currently disabled in code.
  LangSmith is optional (tracing).

---

## 1. Qdrant (shared by both projects)

```bash
docker compose up -d   # see docker-compose.yml — persists via a named volume
```

Verify: `http://localhost:6333/dashboard`

Collection schema (created automatically on first ingestion run): named
vectors `dense` (384-dim, cosine — matches `sentence-transformers/all-MiniLM-L6-v2`)
and `sparse` (BM25, via `Qdrant/bm25` through `fastembed`). Both `ingestion`
and `app` must reference the **same collection name** and the **same
embedding model** — mismatched dimensions or a different embedding model
will silently produce meaningless similarity scores, not an error.

---

## 2. `ingestion/` setup

```bash
cd ingestion
uv python pin 3.12
uv sync
cp .env.example .env   # fill in below
```

**`.env` (flat keys, case-insensitive):**

```env
zeroshot_classification_token_hf=hf_...
supabase_url=https://your-project.supabase.co
supabase_key=sb_secret_...            # secret key (bypasses RLS), NOT the publishable key
qdrant_url=http://localhost:6333
collection_name=corpus                # must match app/'s QDRANT__COLLECTION_NAME exactly
```

AWS S3 (`s3_bucket_name_parsed_doc`, `s3_bucket_name_raw_doc`, `aws_*`) and
`openai_api_key` are defined in the ingestion Settings model but not
required in practice — the S3 upload calls are commented out in
`loaders/loader.py::run()`, and the OpenAI embedding path is fully
commented out in `embedder/embedder.py` (HF is the only embedding provider
actually used). Leave them unset unless you re-enable that code.

**One-time Supabase schema setup** (required before the first ingestion
run — `ingestion/services/upload.py::save_document_metadata()` will fail
with a 404 until this exists): run
[`ingestion/supabase/migrations/20260810120000_create_documents_table.sql`](ingestion/supabase/migrations/20260810120000_create_documents_table.sql)
in your Supabase project's SQL Editor. It creates the `documents` table
(insert-only, one row per ingested file), enables RLS with no policies
(safe default — blocks the publishable key, unaffected by the secret key),
and grants `service_role` explicit table privileges (Postgres does not
grant these automatically on a new table — a missing grant here is the
most likely first error you'll hit, surfacing as `permission denied for
table documents` / `42501`).

Drop source PDFs/DOCX into `ingestion/documents/` — note `load_documents()`
processes **every file** in that folder with no filtering, so remove
anything you don't want ingested in this run — then:

```bash
uv run python -m scripts.main
```

Each document takes a while: Docling OCR conversion alone took ~16-20
minutes for an 800-page textbook on this machine (CPU only), plus several
more minutes for per-chunk embedding calls (one sequential HTTP request per
chunk to HF's hosted inference — ~2,850 chunks for that same textbook).

Per-document flow: convert (Docling) → classify (HF zero-shot, category +
role) → upload raw + parsed to S3 → write document metadata to Supabase →
chunk (HybridChunker + tiktoken) → embed (dense, HF) + BM25 sparse vector →
upsert to Qdrant.

Logs: `ingestion.log` in `ingestion/` (structured JSON, one line per step via
the shared `Reporter`) — check this file, not just the console, when
diagnosing a failed run; some failure detail (e.g. the exact HTTP error
body) only lands there.

**If a run fails partway through**: `run()` generates a fresh `document_id`
per file and per attempt, so a failed run typically leaves a Supabase
`documents` row with no matching Qdrant points (the metadata write happens
before chunking/embedding/storage). Delete that orphaned row before
re-running, or you'll accumulate stale metadata pointing at nothing:
`DELETE FROM public.documents WHERE document_id = '<the id from the log>';`

---

## 3. `app/` setup

```bash
cd app
uv python pin 3.12
uv sync
cp .env.example .env   # fill in below
```

**`.env` (nested keys, `__` delimiter):**

```env
AI_API_KEY=local-dev-api-key   # shared secret checked against incoming X-Api-Key

QDRANT__URL=http://localhost:6333
QDRANT__COLLECTION_NAME=corpus        # must match ingestion/'s collection_name exactly

EMBEDDING__HF_TOKEN=hf_...            # must match the model used in ingestion (all-MiniLM-L6-v2)
EMBEDDING__EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING__EMBED_URL=https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction
EMBEDDING__VECTOR_SIZE=384

RERANKER__HF_TOKEN=hf_...             # HF-hosted cross-encoder, no local model — see known issue below
RERANKER__RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

LLM__GROQ_API_KEY=gsk_...             # services/llm_service.py already uses Groq natively, no swap needed
LLM__MODEL=llama-3.3-70b-versatile

MONGO__URI=mongodb://localhost:27017  # local Docker Mongo for dev; Atlas URI for prod
MONGO__DB_NAME=exobios
MONGO__ASSESSMENTS_COLLECTION=assessments

LANGSMITH__API_KEY=            # optional, enables tracing if set — do NOT rely on any default
                                # here; a prior version of this file shipped a real key hardcoded
                                # as the default, which has since been removed (see git log)
LANGSMITH__PROJECT=exobios-ai
```

Run:

```bash
uv run uvicorn main:app --reload --port 8000
```

Verify: `GET http://localhost:8000/health`

---

## 4. Request flow, end to end

```
Spring Boot --POST /analyze--> app (X-Api-Key checked)
  -> rule_engine (deterministic, no LLM/retrieval)
  -> diagnosis        (embed -> Qdrant hybrid search -> rerank -> LLM)  -> validate -> persist
  -> investigation     (query built from diagnosis)                     -> validate -> persist
  -> treatment_protocol (query built from diagnosis + patient factors)  -> validate -> persist
  -> plan_of_action     (synthesis only, no retrieval)                  -> validate -> persist
  -> response shaped from final state, returned to Spring Boot
```

One MongoDB document per `assessment_id`, updated in place after every
stage — reopening an assessment later reads the same document; no replay
of the graph required.

---

## 5. Quick end-to-end test (no Spring Boot needed)

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: dummy-xai-api-key" \
  -d '{
        "assessmentId": "11111111-1111-1111-1111-111111111111",
        "patientId": "22222222-2222-2222-2222-222222222222",
        "patientComplaint": "high fever for 3 days",
        "complaintCategory": "FEVER",
        "vitals": {"temperature": 102.4, "spo2": 97, "heartRate": 98}
      }'
```

Expect a full `AssessmentResponse` JSON back: deterministic flags,
diagnosis candidates with citations, investigations, treatment protocol,
plan of action. Check Mongo for a matching document under `assessment_id`.

**Verified current behavior**: with only `Biochemistry.pdf` ingested (not a
clinical guideline), expect `diagnosis.insufficient_evidence: true` and
empty candidate/test/treatment lists for symptom-based queries — the
pipeline runs correctly end to end, there's just no clinically-relevant
evidence in the corpus yet to ground a diagnosis on. See
[`docs/POSTMAN_GUIDE.md`](docs/POSTMAN_GUIDE.md) for a full real example
response.

---

## 6. Troubleshooting

- **Empty/irrelevant retrieval results** — check the Qdrant collection
  actually has points (`/dashboard`), and that `complaint_category` filters
  in the request aren't excluding the only chunks present (common with a
  small test corpus — try omitting `complaintCategory` from the request).
- **`insufficient_quota` / 429 from an LLM/embedding call** — billing not
  configured on that provider, or a genuinely small free-tier rate limit
  hit; not a code bug.
- **Vector dimension mismatch on upsert/search** — `ingestion` and `app`
  must use the identical embedding model; confirm `EMBEDDING__` settings
  in `app` match ingestion's embedder.
- **Dependency resolving against the wrong `.venv`** — always `cd` into the
  specific project (`ingestion/` or `app/`) before running `uv` commands;
  don't `source activate` across projects in the same shell.