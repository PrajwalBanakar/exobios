# exobios-ai

The Exobios AI microservice — a FastAPI application that the Spring Boot backend
(`exobios-backend`) calls to analyze submitted patient assessments.

## AI-1 scope

This is **Phase AI-1**: the service skeleton and backend contract integration.
It exists to prove the backend and AI service can talk to each other correctly,
nothing more.

**No clinical AI functionality is implemented in this phase.** There is no
RAG, no vector store (Qdrant), no database, no embeddings, no LLM integration,
no prompt engineering, no medical guideline ingestion, no red-flag detection,
no diagnosis generation, and no risk classification. `POST /analyze` always
returns a safe, deterministic placeholder response — it never makes a
clinical claim about the submitted patient.

## Project structure

```text
exobios-ai/
├── app/
│   ├── main.py                  # FastAPI app factory, middleware, exception handlers
│   ├── api/
│   │   ├── dependencies.py      # X-Api-Key verification
│   │   └── routes/
│   │       ├── analyze.py       # POST /analyze
│   │       └── health.py        # GET /health
│   ├── core/
│   │   ├── config.py            # Typed settings (pydantic-settings)
│   │   ├── exceptions.py        # AppError / AuthenticationError
│   │   └── logging.py           # Structured logging + request-id context
│   ├── middleware/
│   │   └── request_context.py   # Request ID + access-log middleware
│   ├── schemas/
│   │   ├── analyze.py           # AiRequest / AiResponse — mirrors the Java DTOs
│   │   ├── errors.py            # Error envelope
│   │   └── health.py            # Health response
│   └── services/
│       └── analysis_service.py  # Placeholder response generation
├── tests/
├── Dockerfile
├── .dockerignore
├── .env.example
└── pyproject.toml
```

## Prerequisites

- Python 3.12+
- (Optional) Docker Desktop, for container builds

## Local setup (PowerShell)

```powershell
cd exobios-ai

py -3.12 -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install -e ".[dev]"

Copy-Item .env.example .env
# Edit .env and set AI_API_KEY to match the backend's AI_API_KEY / app.ai.api-key

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

`.env` is loaded automatically in local development and is git-ignored. Never
commit a real key — `.env.example` only ships a placeholder.

## Running tests

```powershell
pytest
```

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

## Running both services on the host (no Docker)

Start this service as shown above, then configure the backend
(`exobios-backend/.env`):

```env
AI_SERVICE_URL=http://localhost:8000
AI_API_KEY=<matching-key>
```

## `GET /health`

Liveness only — no API key required, no dependency checks (there are no
external dependencies in AI-1 to check).

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
the full field-by-field contract.

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
- **Backend gets `AiResponse.placeholder()` instead of the stub response** —
  this means `RestAiGateway` couldn't reach this service at all (wrong
  `AI_SERVICE_URL`, service not running, or connection/read timeout). Check
  `GET /health` first.
- **Backend `401`s or falls back on `/analyze`** — confirm both services
  have the *same* `AI_API_KEY` value.
- **Docker container marked unhealthy** — the container health check calls
  `GET /health` on port 8000 internally; check `docker logs <container>` for
  a startup error (most likely a missing `AI_API_KEY`).
