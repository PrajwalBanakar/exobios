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
s3_bucket_name_parsed_doc=...
s3_bucket_name_raw_doc=...
supabase_url=https://your-project.supabase.co
supabase_key=your-service-role-key
aws_access_key_id=...
aws_secret_access_key=...
aws_default_region=...
qdrant_url=http://localhost:6333
collection_name=clinical_corpus
openai_api_key=...   # only if the classification/embedding step still calls OpenAI; see note below
```

Drop source PDFs/DOCX into `ingestion/documents/`, then:

```bash
uv run python -m scripts.main
```

Per-document flow: convert (Docling) → classify (HF zero-shot, category +
role) → upload raw + parsed to S3 → write document metadata to Supabase →
chunk (HybridChunker + tiktoken) → embed (dense, HF) + BM25 sparse vector →
upsert to Qdrant.

Logs: `logs/` (structured, one line per step via the shared `Reporter`).

**Known limitation:** Docling's layout/OCR stage can throw `std::bad_alloc`
on memory-constrained machines, especially on image/table-heavy pages —
this is a compute ceiling, not a pipeline bug (see project notes). Affected
pages are skipped; the document still ingests with whatever content
survives. Re-run on higher-memory hardware for full-fidelity extraction.

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
AI_API_KEY=dummy-xai-api-key   # shared secret checked against incoming X-Api-Key from Spring Boot

QDRANT__URL=http://localhost:6333
QDRANT__COLLECTION_NAME=clinical_corpus

EMBEDDING__HF_TOKEN=hf_...     # must match the model used in ingestion (all-MiniLM-L6-v2)

RERANKER__HF_TOKEN=hf_...      # HF-hosted cross-encoder, no local model

LLM__GEMINI_API_KEY=...        # or swap llm_service.py for the active provider — see note below

MONGO__URI=mongodb+srv://user:pass@cluster.mongodb.net
MONGO__DB_NAME=exobios

LANGSMITH__API_KEY=            # optional, enables tracing if set
LANGSMITH__PROJECT=exobios-ai
```

**Generation provider note:** `services/llm_service.py` currently ships
wired for Gemini. Since generation has been switched to Grok, update that
file's client + `LLMSettings` in `config/settings.py` accordingly (Grok's
API is OpenAI-compatible, so this is a small swap — same
`generate_structured` interface, different client/base URL/model name).
Nothing else in the pipeline needs to change; every node calls
`llm_service.generate_structured(...)` generically.

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