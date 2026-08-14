# exobios-ai / app

FastAPI service implementing the clinical RAG pipeline for exobios-ai.
Called by the Spring Boot backend via `POST /analyze`. Separate from the
`ingestion/` project, which populates the Qdrant corpus this service reads
from.

> **Cross-service contract note:** `docs/api/ai-service-contract.md` (repo
> root) documents an older, flatter `AiResponse` shape
> (status/summary/riskLevel/confidenceScore/redFlags/recommendations/
> modelVersion/source) that `exobios-backend`'s `RestAiGateway` actually
> deserializes `/analyze` responses into. This service currently returns a
> different, richer `AssessmentResponse` shape (see below) — that contract
> doc was written for the AI-1 placeholder phase and was never updated when
> the LangGraph pipeline replaced it. Until one side is reconciled with the
> other, real end-to-end calls from the Spring Boot backend will not
> deserialize correctly. This needs a product decision (compress the rich
> output to the legacy shape, or update the backend DTO), not a unilateral
> code change — see the production-readiness audit for detail.

## Stack

- FastAPI, Pydantic v2 (pydantic-settings for config)
- LangGraph — orchestrates the 5-stage assessment pipeline (deterministic
  rules → diagnosis → investigation → treatment protocol → plan of action)
- LangSmith — optional tracing/observability for graph runs (opt-in; unset
  `LANGSMITH__API_KEY` to disable)
- Qdrant — vector store (hybrid dense + BM25 sparse search, RRF fusion)
- MongoDB — assessment/stage persistence (one document per assessment,
  updated in place after every stage)
- Groq (`llama-3.3-70b-versatile`) — LLM generation calls, forced JSON output
- Hugging Face hosted inference — embeddings (`all-MiniLM-L6-v2`, 384-dim)
  and reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`)

## Project structure

```
app/
├── main.py                      # app factory: middleware, exception handlers, routers
├── core/
│   ├── settings live in config/settings.py, not here
│   ├── logging_config.py           # JSON structured logging, request_id contextvar
│   ├── retry.py                    # retry_with_backoff for transient provider errors
│   ├── exceptions.py                # AppException hierarchy + global + catch-all handlers
│   ├── observability.py              # LangSmith env wiring
│   └── reporting/                   # per-step StepResult logging (FileReporter)
├── config/
│   └── settings.py                  # nested Settings (QdrantSettings, LLMSettings, ...)
├── api/
│   ├── dependencies.py               # verify_api_key
│   └── routes/
│       ├── analyze.py
│       └── health.py                 # /health (liveness), /health/ready (dependency check)
├── schemas/
│   ├── request.py                    # AiRequest — mirrors Java DTO, physiological bounds
│   ├── response.py                   # AssessmentResponse — current (not AiResponse) contract
│   ├── state_object.py               # AssessmentState — the LangGraph state object
│   └── stages/                       # per-stage result schemas + SupportingCitation
├── graph/
│   ├── builder.py                    # node/edge wiring only, no logic
│   ├── nodes/
│   │   ├── rule_engine.py             # pre-graph deterministic step
│   │   ├── diagnosis.py
│   │   ├── investigation.py
│   │   ├── treatment.py
│   │   ├── plan_of_action.py
│   │   └── validation.py              # citation verification + risk-floor re-check
│   └── tools/
│       └── retrieval.py               # retrieve_and_rerank — shared by 3 nodes
├── services/
│   ├── qdrant_service.py
│   ├── embedding_service.py
│   ├── reranker_service.py
│   └── llm_service.py
├── repositories/
│   ├── assesment.py                   # raw Mongo reads/writes (note: filename typo, live as-is)
│   └── persistence.py                 # persist_state — snapshot-per-stage
└── middleware/
    └── request_context.py             # request_id assignment (reuses caller's X-Request-Id), access logging
```

`tests/` lives at the repo root (`exobios-ai/tests/`), not under `app/` —
see the root `pytest.ini` for why (`pythonpath = app` makes app's unqualified
internal imports resolve when tests run from the repo root).

## Layering rules

- `services/` — one external system per file (Qdrant client, embedding API,
  reranker API, LLM API). No domain knowledge. Input in, output out.
- `graph/tools/` — composes 2+ services into one reusable operation (e.g.
  embed → search → rerank). Still no domain knowledge — doesn't know which
  node is calling it.
- `graph/nodes/` — the only layer with domain logic. Decides query text,
  filters, prompts, what to do with a stage's result, writes to state.
  Calls tools and services; never called by them.
- `graph/builder.py` — pure wiring (which nodes, what order, what edges).
  No logic beyond graph structure.
- `repositories/` — raw Mongo reads/writes only, no business logic.

Test: adding a new capability (e.g. a reranker) should touch exactly one
service + the one tool that composes it. If it forces changes across every
node, logic is misplaced too high up.

## Auth

`X-Api-Key` header, checked via a FastAPI dependency
(`api/dependencies.py::verify_api_key`), compared with
`secrets.compare_digest`. Must match `AI_API_KEY` on the Spring Boot side
exactly. A missing header and a wrong header both map to the same 401
`AuthenticationError` (not two different status codes). Not CORS — this is a
server-to-server shared secret, no browser involved.

## Groundedness / citation verification

Every citation an LLM stage returns is cross-checked in
`graph/nodes/validation.py` against the chunks actually retrieved for that
stage (`AssessmentState.retrieved_evidence`). A citation whose `chunk_id`
wasn't retrieved is dropped (never trusted from the LLM's own text), and any
diagnosis candidate / investigation test / treatment step left with no
verified citation is dropped too. If diagnosis ends up with zero verified
candidates, `insufficient_evidence` is force-set to `True` in code — this
does not depend on the LLM correctly setting that flag itself. Diagnosis
also skips the LLM call entirely (returns `insufficient_evidence=True`
directly) when retrieval returns nothing at all, so an empty knowledge base
never reaches the point of the model free-associating from its own training
data.

## Exception boundary

All application errors subclass `AppException` (`core/exceptions.py`), each
with a `status_code` and `error_code`. One global exception handler
(registered in `main.py`) catches every subclass and shapes the response.
A second, catch-all handler (`handle_unexpected_exception`) catches anything
else (a bug outside the `AppException` hierarchy) and still returns a
structured 500 with a `request_id`, instead of leaking a bare
Starlette/stack-trace response. `InsufficientEvidenceException` is a 200,
not a failure — a legitimate "not enough retrieved evidence" outcome, not a
system error (though in practice the current code represents this via
`DiagnosisResult.insufficient_evidence`, not by raising that exception).

## Logging

Structured JSON via `core/logging_config.py` (`JsonFormatter`), rotating at
10MB/5 backups so `app.log` doesn't grow unbounded. `request_id` is set once
per request in `middleware/request_context.py` (reusing the caller's
`X-Request-Id`/`X-Correlation-Id` header when present, for cross-service
trace correlation) via a `contextvars` context, then automatically included
in every log line for that request without being passed manually through
function calls. Set `LOG_LEVEL` to override the default `INFO`.

## Resilience

`core/retry.py::retry_with_backoff` wraps the embedding, reranker, LLM, and
Qdrant calls in `services/` — retries transient failures (connection
errors/timeouts, HTTP 429/500/502/503/504, Groq's own retryable error
classes) with exponential backoff, and re-raises immediately on anything
else. Mongo's client has explicit 5s connect/server-selection timeouts (not
pymongo's 30s default), so a downed Mongo fails fast rather than stalling
every request for 30s.

## Setup

```bash
cd app
uv sync
cp .env.example .env    # fill in Qdrant, HF, Groq, Mongo, (optional) LangSmith keys
uv run uvicorn main:app --reload --port 8000
```

## Environment variables

Nested via `env_nested_delimiter="__"` — see `.env.example` for the
authoritative list. Summary:

| Variable | Purpose |
|---|---|
| `AI_API_KEY` | Shared secret checked against incoming `X-Api-Key` |
| `QDRANT__URL`, `QDRANT__COLLECTION_NAME` | Vector store connection |
| `EMBEDDING__HF_TOKEN` | Hugging Face token for the embedding model |
| `RERANKER__HF_TOKEN` | Hugging Face token for the reranker model |
| `LLM__GROQ_API_KEY`, `LLM__MODEL` | Generation calls (Groq) |
| `MONGO__URI`, `MONGO__DB_NAME` | Assessment/stage persistence |
| `LANGSMITH__API_KEY`, `LANGSMITH__PROJECT` | Optional LangSmith tracing (leave blank to disable) |
| `LOG_LEVEL` | Optional, defaults to `INFO` |

## Tests

```bash
cd exobios-ai       # not app/ — see the "tests/" note above
uv run --project app pytest tests/ -v
```

Every external dependency (Qdrant, Mongo, HF, Groq) is mocked in
`tests/conftest.py`'s `mock_external_services` autouse fixture — the suite
needs no live services and runs in well under a second.
