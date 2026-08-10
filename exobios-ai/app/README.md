# exobios-ai / app

FastAPI service implementing the clinical RAG pipeline for exobios-ai.
Called by the Spring Boot backend via `POST /analyze`. Separate from the
`ingestion/` project, which populates the Qdrant corpus this service reads
from.

## Stack

- FastAPI, Pydantic v2 (pydantic-settings for config)
- LangGraph — orchestrates the 4-stage assessment pipeline
- LangSmith — tracing/observability for every graph run
- Qdrant — vector store (hybrid dense + sparse search)
- Supabase (Postgres) — assessment/stage persistence, document registry
- Anthropic/OpenAI SDK — LLM generation calls

## Project structure

```
app/
├── main.py                      # app factory only
├── core/
│   ├── config.py                # nested Settings (QdrantSettings, LLMSettings, ...)
│   ├── logging.py                # JSON structured logging, request_id contextvar
│   ├── exceptions.py              # AppException hierarchy + global handler
│   └── observability.py            # LangSmith env wiring
├── api/
│   ├── dependencies.py             # verify_api_key, other route-level guards
│   └── routes/
│       ├── analyze.py
│       └── health.py
├── schemas/
│   ├── request.py                  # AiRequest — mirrors Java DTO exactly
│   ├── response.py                 # external response contract
│   ├── state.py                    # AssessmentState — the LangGraph state object
│   └── errors.py
├── graph/
│   ├── builder.py                  # node/edge wiring only, no logic
│   ├── nodes/
│   │   ├── rule_engine.py           # pre-graph deterministic step
│   │   ├── diagnosis.py
│   │   ├── investigation.py
│   │   ├── treatment.py
│   │   ├── plan_of_action.py
│   │   └── validation.py
│   └── tools/
│       └── retrieval.py             # retrieve_and_rerank — shared by 3 nodes
├── services/
│   ├── qdrant_service.py
│   ├── embedding_service.py
│   ├── reranker_service.py
│   ├── llm_service.py
│   └── persistence_service.py
├── repositories/
│   └── assessment_repository.py     # raw Supabase reads/writes only
├── middleware/
│   └── request_context.py           # request_id assignment, access logging
└── tests/
```

## Layering rules

- `services/` — one external system per file (Qdrant client, embedding API,
  reranker API, LLM API, Supabase). No domain knowledge. Input in, output out.
- `graph/tools/` — composes 2+ services into one reusable operation (e.g.
  embed → search → rerank). Still no domain knowledge — doesn't know which
  node is calling it.
- `graph/nodes/` — the only layer with domain logic. Decides query text,
  filters, prompts, what to do with a stage's result, writes to state.
  Calls tools and services; never called by them.
- `graph/builder.py` — pure wiring (which nodes, what order, what edges).
  No logic beyond graph structure.
- `repositories/` — raw Supabase queries only, no business logic. Optional
  separation from `services/persistence_service.py` at current scale.

Test: adding a new capability (e.g. a reranker) should touch exactly one
service + the one tool that composes it. If it forces changes across every
node, logic is misplaced too high up.

## Auth

`X-Api-Key` header, checked via a FastAPI dependency
(`api/dependencies.py::verify_api_key`), compared with
`secrets.compare_digest`. Must match `AI_API_KEY` on the Spring Boot side
exactly. Not CORS — this is a server-to-server shared secret, no browser
involved.

## Exception boundary

All application errors subclass `AppException` (`core/exceptions.py`), each
with a `status_code` and `error_code`. One global exception handler
(registered in `main.py`) catches every subclass and shapes the response —
no route or node manually formats an error. `InsufficientEvidenceException`
is a 200, not a failure — a legitimate "not enough retrieved evidence"
outcome, not a system error.

## Logging

Structured JSON via `core/logging.py`. `request_id` is set once per request
in `middleware/request_context.py` via a `contextvars` context, then
automatically included in every log line for that request without being
passed manually through function calls.

## Setup

```bash
cd app
uv sync
cp .env.example .env    # fill in Qdrant, LLM, Supabase, LangSmith keys
uv run uvicorn main:app --reload --port 8000
```

## Environment variables

| Variable | Purpose |
|---|---|
| `AI_API_KEY` | Shared secret checked against incoming `X-Api-Key` |
| `QDRANT_URL`, `QDRANT_COLLECTION_NAME` | Vector store connection |
| `LLM_API_KEY`, `LLM_MODEL` | Generation calls |
| `SUPABASE_URL`, `SUPABASE_KEY` | Assessment/stage persistence |
| `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` | LangSmith tracing |