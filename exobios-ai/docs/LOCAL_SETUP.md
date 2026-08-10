# Exobios AI Service — Local Setup Guide (Windows)

This guide takes you from a fresh clone to a running FastAPI service you can
test in Postman. It assumes Windows 11 with PowerShell.

## 1. Prerequisites

- **Git**
- **Python 3.13** (uv will download/manage this for you automatically — a
  system Python is only needed to bootstrap `uv` itself)
- **uv** (Python package/env manager) — install with:
  ```powershell
  python -m pip install --user uv
  ```
  or the official standalone installer:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  Then make sure `uv` is on your `PATH` (restart your terminal, or add
  `%APPDATA%\Python\Python3xx\Scripts` to PATH). Verify:
  ```powershell
  uv --version
  ```
- **Docker Desktop** (for local Qdrant + MongoDB) — must be running before
  you start the service.
- **Postman** (for API testing).
- Accounts (see section 5): **Hugging Face**, **Groq**. Optional:
  **Supabase**, **AWS** (only if you'll run the ingestion pipeline).

## 2. Clone

```powershell
git clone https://github.com/PrajwalBanakar/exobios.git
cd exobios/exobios-ai
```

You're already in this state if you're reading this from the
`integration/om-ai-service` branch.

## 3. Environment files

```powershell
Copy-Item app\.env.example app\.env -ErrorAction SilentlyContinue
# app\.env already exists in this branch with local-dev defaults filled in
# for AI_API_KEY / Qdrant / Mongo — you still need to add your own
# Hugging Face token and Groq API key (see section 5).
```

If you'll run the ingestion CLI too:

```powershell
Copy-Item ingestion\.env.example ingestion\.env
```

## 4. Start local infrastructure

From `exobios-ai/`:

```powershell
docker compose up -d
docker compose ps
```

This starts:

- **Qdrant** on `localhost:6333` (REST) / `6334` (gRPC)
- **MongoDB** on `localhost:27017`

## 5. External accounts / API keys

| Service | Why | Where to get it | Required now? |
|---|---|---|---|
| Hugging Face | Embeddings + reranker (hosted inference) | https://huggingface.co/settings/tokens — free account, "Read" token is enough | **Yes** — `/analyze` fails without it |
| Groq | LLM (diagnosis/investigation/treatment/plan reasoning) | https://console.groq.com — free tier | **Yes** — `/analyze` fails without it |
| Supabase | Document metadata storage (ingestion pipeline only) | https://supabase.com — free tier | Only if running `ingestion/` |
| AWS S3 | Raw/parsed document storage (ingestion pipeline) | AWS account, IAM user | No — upload calls are currently disabled in code |

Fill these into `app/.env`:

```
EMBEDDING__HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
RERANKER__HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx   # can reuse the same token
LLM__GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

## 6. Install dependencies

```powershell
cd app
uv sync --dev
```

This creates `app\.venv` and installs everything pinned in `app\uv.lock`.

## 7. Run the service

**Important**: `app/main.py` uses unqualified imports (`from api.routes import ...`),
so it must be run **with `app/` itself as the working directory** — not as
`app.main:app` from the repo root.

```powershell
cd exobios-ai\app
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 8. Verify

- Health: http://localhost:8000/health → `{"status":"UP","service":"exobios-ai-app","version":"0.1.0"}`
- Swagger UI: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

## 9. Run tests / lint

```powershell
cd exobios-ai\app
uv run ruff check .
```

```powershell
cd exobios-ai
uv run --project app pytest tests/ -v
```

**Known issue**: the top-level `tests/` currently fail to even collect
(`ModuleNotFoundError: No module named 'api'`) because `tests/conftest.py`
imports `from app.main import app`, which conflicts with `app/main.py`'s own
unqualified-import style (see section 7). The tests also assert an older,
now-superseded placeholder API contract. This is tracked as tech debt — see
the integration report. Do not spend time trying to fix these without a
larger rewrite; it's not required to run/test the service.

## 10. Test through Postman

See `docs/POSTMAN_GUIDE.md` for exact requests, headers, and sample bodies.

## 11. Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `only one usage of each socket address... 8000` | Another process already bound to port 8000 | `netstat -ano \| findstr :8000` then `Stop-Process -Id <pid> -Force`, or use `--port 8001` |
| `Qdrant client version ... incompatible with server version` | Local Qdrant image older than the pinned `qdrant-client` version | Already fixed in `docker-compose.yml` (pinned to `v1.12.4`); run `docker compose up -d qdrant` to recreate |
| `pydantic_core._pydantic_core.ValidationError` on startup mentioning `embedding.hf_token` / `llm.groq_api_key` / `mongo.uri` | Missing/blank required setting in `app/.env` | Fill in the field — these have no defaults by design |
| `/analyze` returns `502 retrieval_failed: ... 401 Unauthorized ... huggingface.co` | `EMBEDDING__HF_TOKEN` / `RERANKER__HF_TOKEN` missing or invalid | Add a real Hugging Face token |
| `/analyze` returns `502 llm_generation_failed` | `LLM__GROQ_API_KEY` missing/invalid, or Groq rate-limited | Add a real Groq key; check https://console.groq.com usage |
| `pymongo.errors.InvalidURI` at startup | Malformed `MONGO__URI` | Must be a full `mongodb://host:port` URI even for local dev |
| Empty/near-empty diagnosis results (`insufficient_evidence: true`) | The Qdrant `corpus` collection has no ingested documents yet | Expected until you run the ingestion pipeline (see `docs/ARCHITECTURE.md`) — this is the grounding safeguard working correctly, not a bug |
