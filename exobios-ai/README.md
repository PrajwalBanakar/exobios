# exobios-ai

The Exobios AI microservice — a FastAPI application that the Spring Boot
backend (`exobios-backend`) calls to analyze submitted patient assessments.

## Status at a glance

There are two separate things living in this repo right now, and it's easy to
conflate them:

| | Status |
|---|---|
| **`POST /analyze` (the HTTP API the backend calls)** | Still a stub. Always returns a safe, deterministic placeholder — no RAG, no LLM call, no clinical claim. This is intentional: the backend integration was proven first (AI-1), before any AI logic existed. |
| **The RAG pipeline (ingestion → embeddings → retrieval → prompting → generation)** | Fully implemented and testable end-to-end, but **not yet wired into `POST /analyze`**. It's exercised today via [`scripts/demo_pipeline.py`](scripts/demo_pipeline.py), not through the API. |

In other words: the clinical AI logic exists and works, it's just not plugged
into the endpoint the backend hits yet. Connecting them is the next phase of
work.

## How the pieces fit together (data flow)

```text
                                   ┌─────────────────────────────┐
                                   │   Clinical guideline PDF     │
                                   │  (imnci_chart_booklet.pdf)  │
                                   └───────────────┬──────────────┘
                                                    │
                                                    ▼
 app/ingestion/     load → parse → clean → chunk → embed → upsert into Qdrant
 (pdf/docx/md/txt        │        │         │         │
  parsers, chunker,      LocalFileLoader → ParserRegistry → TextCleaner →
  in-memory registry)    RecursiveChunker → EmbeddingService → QdrantVectorStore

 app/embeddings/     EmbeddingProvider (OpenAI or Gemini) + QdrantVectorStore,
                     wired together by build_default_embedding_service()

                                                    │  (offline / one-time per document)
                                                    ▼
                                        ┌───────────────────────┐
                                        │   Qdrant collection    │
                                        │   "exobios_chunks"     │
                                        └───────────┬────────────┘
                                                    │
                     ── at request time, per patient case ──
                                                    │
                                                    ▼
 app/retrieval/      embed the query → SemanticRetriever searches Qdrant →
                     ScoreReranker → top-N relevant chunks
                     (build_default_retrieval_service())
                                                    │
                                                    ▼
 app/prompting/      RagPromptBuilder assembles a token-budgeted Jinja2
                     prompt (patient context + cited retrieved chunks) using
                     ContextFormatter; PromptService drives retrieval + build
                     (build_default_prompt_service())
                                                    │
                                                    ▼
 app/generation/     LLMProvider (OpenAI or Gemini) generates a structured,
                     schema-validated clinical draft (possible conditions,
                     risk assessment, red flags, recommended actions,
                     citations back to source chunks) via GenerationService +
                     ResponseValidator (build_default_generation_service())
                                                    │
                                                    ▼
                                    (not yet connected — see Status above)
                                                    │
                                                    ▼
 app/services/        analysis_service.py — what POST /analyze actually
 analysis_service.py  calls today: a placeholder AiResponse, independent of
                      everything above.
```

Each stage is its own module with a `factory.py` **composition root** —
`build_default_*_service()` — that wires the real collaborators (OpenAI/Gemini
clients, Qdrant client, Jinja2 environment) from `Settings`. Tests and
alternative wiring inject fakes through the same constructor arguments instead
of hitting the network.

### Provider abstraction (OpenAI vs. Gemini)

Both `app/embeddings/providers/` and `app/generation/providers/` define a
provider interface (`base.py`) with an OpenAI implementation and a Gemini
implementation. Every factory picks Gemini when `GEMINI_API_KEY` is set and
falls back to OpenAI otherwise — no other code changes needed. Gemini exists
as a free-tier alternative for local dev/demo use; ingestion and retrieval
must use the *same* provider/model, since embeddings from different models
aren't comparable in vector search (the factories read the same setting, so
this stays consistent automatically).

## Project structure

```text
exobios-ai/
├── app/
│   ├── main.py                    # FastAPI app factory — only wires up health + analyze
│   ├── api/
│   │   ├── dependencies.py        # X-Api-Key verification
│   │   └── routes/
│   │       ├── analyze.py         # POST /analyze (stub response, see Status)
│   │       └── health.py          # GET /health
│   ├── core/
│   │   ├── config.py              # Typed settings (pydantic-settings) for every stage below
│   │   ├── exceptions.py          # AppError / AuthenticationError
│   │   └── logging.py             # Structured logging + request-id context
│   ├── middleware/
│   │   └── request_context.py     # Request ID + access-log middleware
│   ├── schemas/
│   │   ├── analyze.py             # AiRequest / AiResponse — mirrors the Java DTOs
│   │   ├── errors.py              # Error envelope
│   │   └── health.py              # Health response
│   ├── services/
│   │   └── analysis_service.py    # What POST /analyze actually calls: placeholder response
│   │
│   ├── ingestion/                 # Document ingestion pipeline (AI-2)
│   │   ├── loaders/               # LocalFileLoader — reads a file off disk
│   │   ├── parsers/                # pdf / docx / markdown / txt parsers + registry
│   │   ├── cleaning/              # TextCleaner — normalizes extracted text
│   │   ├── chunkers/               # RecursiveChunker — splits into overlapping chunks
│   │   ├── registry/               # InMemoryDocumentRegistry — tracks ingested documents
│   │   ├── models/                 # Document / Chunk / IngestionResult
│   │   └── services/               # IngestionService + factory.py (composition root)
│   │
│   ├── embeddings/                 # Embeddings + vector store pipeline (AI-3)
│   │   ├── providers/               # OpenAIEmbeddingProvider / GeminiEmbeddingProvider
│   │   ├── vectorstores/            # QdrantVectorStore
│   │   ├── models/                  # Embedding model
│   │   ├── services/                # EmbeddingService
│   │   └── factory.py               # build_default_embedding_service()
│   │
│   ├── retrieval/                   # Semantic retrieval engine (AI-4)
│   │   ├── retrievers/                # SemanticRetriever (queries Qdrant)
│   │   ├── ranking/                   # ScoreReranker
│   │   ├── models/                    # SearchRequest / retrieval results
│   │   ├── services/                  # RetrievalService
│   │   └── factory.py                 # build_default_retrieval_service()
│   │
│   ├── prompting/                    # Prompt construction (AI-5)
│   │   ├── builders/                   # RagPromptBuilder (Jinja2, token-budgeted)
│   │   ├── formatting/                 # ContextFormatter — formats cited chunks
│   │   ├── templates/                  # Jinja2 prompt templates (e.g. diagnosis)
│   │   ├── models/                     # PromptRequest / PatientContext / PromptResponse
│   │   ├── services/                   # PromptService
│   │   └── factory.py                  # build_default_prompt_service()
│   │
│   └── generation/                   # LLM generation pipeline (AI-6)
│       ├── providers/                  # OpenAIProvider / GeminiProvider
│       ├── validation/                 # ResponseValidator — validates LLM JSON output
│       ├── models/                     # GenerationRequest / GenerationResponse / usage
│       ├── services/                   # GenerationService
│       └── factory.py                  # build_default_generation_service()
│
├── scripts/
│   └── demo_pipeline.py           # Runs the full pipeline end-to-end outside the API
├── imnci_chart_booklet.pdf        # Sample clinical guideline used by the demo script
├── tests/                         # Mirrors app/ — one directory per pipeline stage
├── Dockerfile
├── .dockerignore
├── .env.example
└── pyproject.toml
```

## Prerequisites

- Python 3.12+
- (Optional) Docker Desktop, for container builds and/or running Qdrant locally
- An OpenAI API key, **or** a Gemini API key (free tier) — see
  [Environment variables](#environment-variables)

## Local setup (PowerShell)

```powershell
cd exobios-ai

py -3.12 -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install -e ".[dev]"

Copy-Item .env.example .env
# Edit .env:
#  - Set AI_API_KEY to match the backend's AI_API_KEY / app.ai.api-key
#  - Set OPENAI_API_KEY or GEMINI_API_KEY (at least one is required)

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `APP_NAME` | `exobios-ai` | Reported in `/health` |
| `APP_ENV` | `development` | Free-form environment label |
| `APP_VERSION` | `0.1.0` | Reported in `/health` |
| `HOST` | `0.0.0.0` | Uvicorn bind host |
| `PORT` | `8000` | Uvicorn bind port |
| `AI_API_KEY` | *(required, no default)* | Must match the backend's `AI_API_KEY` / `app.ai.api-key` exactly. The app refuses to start without it. |
| `LOG_LEVEL` | `INFO` | Standard Python logging level |
| `ENABLE_API_DOCS` | `true` | Set to `false` in production to disable `/docs`, `/redoc`, `/openapi.json` |
| `OPENAI_API_KEY` | *(required unless `GEMINI_API_KEY` is set)* | Used by the embeddings and generation providers. |
| `GEMINI_API_KEY` | *(required unless `OPENAI_API_KEY` is set)* | Free-tier alternative — when set, embeddings/generation/retrieval factories wire up Gemini instead of OpenAI. Exactly one of the two provider keys must be set. |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Passed to whichever embedding provider is active |
| `EMBEDDING_BATCH_SIZE` | `100` | Chunks embedded per API call |
| `QDRANT_URL` | `http://localhost:6333` | Local Qdrant (see `docker-compose.yml`) |
| `QDRANT_API_KEY` | *(none)* | Optional — local Qdrant has no auth by default |
| `QDRANT_COLLECTION` | `exobios_chunks` | Vector store collection name |
| `RETRIEVAL_TOP_K` | `20` | Chunks fetched from Qdrant before reranking |
| `MIN_SIMILARITY_SCORE` | `0.0` | Score floor applied during retrieval |
| `MAX_RETURNED_CHUNKS` | `10` | Chunks returned after reranking |
| `MAX_PROMPT_TOKENS` | `4000` | Total prompt token budget |
| `MAX_CONTEXT_TOKENS` | `2000` | Token budget reserved for cited chunks within the prompt |
| `RESERVED_RESPONSE_TOKENS` | `500` | Tokens reserved for the model's response |
| `DEFAULT_PROMPT_TEMPLATE` | `diagnosis` | Jinja2 template name under `app/prompting/templates/` |
| `LLM_MODEL` | `gpt-4.1-mini` | Reuses the active provider's key — no separate LLM API key setting |
| `LLM_TEMPERATURE` | `0.2` | |
| `LLM_MAX_OUTPUT_TOKENS` | `1500` | |
| `LLM_TIMEOUT_SECONDS` | `30.0` | |
| `LLM_MAX_RETRIES` | `2` | |
| `LLM_CONTEXT_WINDOW` | *(unset)* | Optional — when set, `GenerationService` runs a prompt-budget pre-flight check against it |

`.env` is loaded automatically in local development and is git-ignored. Never
commit a real key — `.env.example` only ships placeholders.

## Running the RAG pipeline demo

[`scripts/demo_pipeline.py`](scripts/demo_pipeline.py) runs the entire flow
described above against a real Qdrant instance and a real LLM: it ingests
`imnci_chart_booklet.pdf` (skipping ingestion if Qdrant already has vectors
from a prior run), then runs a sample sick-child case through retrieval,
prompting, and generation, printing the model's structured clinical draft
with citations.

```powershell
# Requires Qdrant running (see Docker section) and OPENAI_API_KEY or
# GEMINI_API_KEY set in .env
python scripts/demo_pipeline.py
```

## Running tests

```powershell
pytest
```

Tests are organized to mirror `app/`: `tests/ingestion/`, `tests/embeddings/`,
`tests/retrieval/`, `tests/prompting/`, `tests/generation/`, plus top-level
tests for the API surface (`test_analyze.py`, `test_authentication.py`,
`test_health.py`). Each pipeline stage also has a `test_pipeline_integration.py`
covering its factory-wired composition, and `test_factory.py` covering
provider selection (OpenAI vs. Gemini).

## Ruff

```powershell
ruff check .
ruff format .
```

## Docker

Build and run standalone:

```powershell
docker build -t exobios-ai .
docker run -p 8000:8000 -e AI_API_KEY=local-dev-key-12345 exobios-ai
```

Or via the backend's Compose stack (recommended — starts Postgres, the
backend, and this service together):

```powershell
cd ../exobios-backend
docker compose up -d
```

The Compose file builds this service from `../exobios-ai` and gives it the
service name `ai-service`. Inside the Compose network, the backend reaches it
at `http://ai-service:8000`, **not** `localhost` — Compose environment
variables set this by default (`AI_SERVICE_URL=http://ai-service:8000`), but
if your `exobios-backend/.env` already defines `AI_SERVICE_URL` (e.g. copied
from `.env.example` for a non-Docker setup), that value takes precedence and
will point the containerized backend at itself. Remove or comment out that
line in `exobios-backend/.env` before running `docker compose up`, or export
`AI_SERVICE_URL=http://ai-service:8000` explicitly.

Qdrant itself is expected to run as its own container (see
`docker-compose.yml`) — the RAG pipeline modules (`app/embeddings`,
`app/retrieval`) are not exercised by the `POST /analyze` container at all
today (see Status above); Qdrant is only needed for the demo script and tests
that opt into a real vector store.

## Running both services on the host (no Docker)

Start this service as shown above, then configure the backend
(`exobios-backend/.env`):

```env
AI_SERVICE_URL=http://localhost:8000
AI_API_KEY=<matching-key>
```

## `GET /health`

Liveness only — no API key required, no dependency checks (Qdrant/OpenAI/
Gemini reachability is not checked here, since `POST /analyze` doesn't call
them yet either).

```bash
curl http://localhost:8000/health
```

```json
{"status": "UP", "service": "exobios-ai", "version": "0.1.0"}
```

## `POST /analyze`

Requires `X-Api-Key`. Accepts the backend's `AiRequest` shape and always
returns the same safe placeholder `AiResponse` — see
[`docs/api/ai-service-contract.md`](../docs/api/ai-service-contract.md) for
the full field-by-field contract. It does **not** call the RAG pipeline
described above; see [Status at a glance](#status-at-a-glance).

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: local-dev-key-12345" \
  -d '{
        "assessmentId": "11111111-1111-1111-1111-111111111111",
        "patientId": "22222222-2222-2222-2222-222222222222",
        "symptoms": []
      }'
```

```json
{
  "status": "PENDING",
  "summary": "AI analysis pipeline is not implemented in this service version.",
  "riskLevel": null,
  "confidenceScore": 0.0,
  "redFlags": "",
  "recommendations": "",
  "modelVersion": "stub-v0.1.0",
  "source": "exobios-ai-stub"
}
```

## Security notes

- `X-Api-Key` is compared using `secrets.compare_digest` (constant-time).
- The service never logs the patient complaint, symptom descriptions, past
  illnesses, medications, allergies, or any other patient-identifying detail.
  Logs only ever include: request ID, assessment ID, complaint category,
  symptom count, whether vitals were provided, response status, HTTP status,
  and duration.
- Error responses never include stack traces, file paths, environment
  variables, or secrets.
- `ENABLE_API_DOCS=false` disables Swagger/OpenAPI exposure entirely — set
  this in production.

## Troubleshooting

- **App won't start / `AI_API_KEY` validation error** — `AI_API_KEY` is
  required with no default; set it in `.env` or the environment.
- **App won't start / "Set either OPENAI_API_KEY or GEMINI_API_KEY"** — at
  least one provider key is required; set one of them in `.env`.
- **Backend gets `AiResponse.placeholder()` instead of the stub response** —
  this means `RestAiGateway` couldn't reach this service at all (wrong
  `AI_SERVICE_URL`, service not running, or connection/read timeout). Check
  `GET /health` first.
- **Backend `401`s or falls back on `/analyze`** — confirm both services
  have the *same* `AI_API_KEY` value.
- **Docker container marked unhealthy** — the container health check calls
  `GET /health` on port 8000 internally; check `docker logs <container>` for
  a startup error (most likely a missing `AI_API_KEY`).
- **`scripts/demo_pipeline.py` fails to connect to Qdrant** — it expects
  Qdrant reachable at `QDRANT_URL` (default `http://localhost:6333`); start
  it via the backend's Compose stack or run a standalone Qdrant container.
