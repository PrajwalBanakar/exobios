# Exobios AI Service — Architecture (post Om-integration)

## System flow

```
Postman / (later) Spring Boot
        |  POST /analyze  { X-Api-Key }
        v
FastAPI (app/main.py)
        |  RequestContextMiddleware (request id, timing log)
        v
verify_api_key  ->  401 if missing/wrong X-Api-Key
        v
AssessmentState(assessment_id, patient_input=AiRequest)
        v
LangGraph pipeline (app/graph/builder.py), linear, 6 stages:

  rule_engine            deterministic vitals thresholds -> DeterministicFlag[]
        v                (no LLM, no retrieval — hard safety floor)
  diagnosis        -+--> embed query (HF) -> Qdrant hybrid search -> rerank (HF)
        v           |    -> Groq LLM (grounded-only prompt) -> DiagnosisResult
  validate + persist +
        v           |
  investigation     -+--> same retrieval pattern, per top-3 diagnoses
        v           |
  validate + persist +
        v           |
  treatment_protocol-+--> same retrieval pattern, per top-2 diagnoses
        v           |
  validate + persist +
        v
  plan_of_action          no retrieval; synthesizes from all prior stages;
        v                 code re-enforces risk_floor from rule_engine
  validate + persist  (MongoDB, one doc per assessment, upserted every stage)
        v
AssessmentResponse (nested, snake_case) <- FastAPI serializes as JSON
```

Every stage after `rule_engine` writes a full snapshot of the in-progress
`AssessmentState` to MongoDB (`repositories/persistence.py::persist_state`),
so a crash mid-run leaves the completed stages recoverable (though the graph
itself has no LangGraph checkpointer wired — resuming a partial run means
calling `/analyze` again from scratch, not resuming automatically).

## Two independent projects

`exobios-ai/` contains two separately-run Python projects that only share a
Qdrant collection as a data contract:

- **`app/`** — the FastAPI service above. This is what you run for Postman
  testing and what Spring Boot will eventually call.
- **`ingestion/`** — a standalone offline CLI tool: PDF -> Docling (OCR-capable
  conversion) -> zero-shot classification (complaint category / applicable
  roles) -> chunking (Docling `HybridChunker` + tiktoken) -> embedding (same
  HF model as `app/`) -> Qdrant upsert. Populates the corpus `app/` retrieves
  against. Not imported by `app/` at runtime.

## External systems and their responsibilities

| System | Used by | Responsibility | Local dev | Production |
|---|---|---|---|---|
| Qdrant | `app/`, `ingestion/` | Vector store: dense (384-dim, HF MiniLM) + sparse (BM25) hybrid search over document chunks | Docker (`docker-compose.yml`) | Managed Qdrant Cloud or self-hosted |
| MongoDB | `app/` | Persists `AssessmentState` snapshots per stage, keyed by `assessment_id` | Docker (`docker-compose.yml`) | MongoDB Atlas or self-hosted |
| Hugging Face (hosted inference) | `app/` (embedding + reranker), `ingestion/` (embedding + zero-shot classification) | Dense embeddings, cross-encoder reranking, zero-shot document classification | Free HF account + token | Same, or self-hosted inference for cost/latency |
| Groq | `app/` | LLM calls (`llama-3.3-70b-versatile`) for diagnosis/investigation/treatment/plan reasoning, structured JSON output | Free tier | Paid tier, consider a fallback provider |
| Supabase | `ingestion/` | Document metadata storage (title, category, applicable roles, file location) | Free tier project | Same, or replace with the app's own Mongo if redundant (see note below) |
| AWS S3 | `ingestion/` (code exists, calls currently commented out) | Would store raw + parsed source documents | Not required — documents stay local in `ingestion/documents/` | Required if source PDFs need durable, non-local storage |
| LangSmith | `app/` (optional) | LangGraph run tracing/observability | Optional, off by default | Optional |

**Note on Supabase vs Mongo redundancy**: `ingestion/` uses Supabase purely
for document metadata (title, category, roles) while `app/` uses MongoDB for
assessment persistence — these don't overlap today, but they are two
different managed databases for two halves of the same product. Consolidating
onto one (most likely Mongo, since `app/` already depends on it) is a
reasonable simplification for later, not urgent now.

## Grounding / hallucination safeguards (Step 22 check)

- Every retrieval-backed node (`diagnosis`, `investigation`, `treatment`)
  prompts the LLM to reason **only** from retrieved excerpts and to set
  `insufficient_evidence=true` with an empty candidate list rather than guess
  when evidence is thin — this is enforced in the prompt text, not in code.
- `validate_diagnosis`/etc. (`app/graph/nodes/validation.py`) checks that
  every citation has a non-empty excerpt, but **does not** independently
  verify the LLM actually respected `insufficient_evidence` or refuse to
  publish ungrounded claims — grounding compliance is currently prompt-only,
  not code-enforced. If the LLM ignores the instruction, nothing downstream
  catches it.
- The one exception is the deterministic risk floor: `rule_engine`'s vitals
  thresholds are re-checked and force-overridden in code in both
  `plan_of_action_node` and `validate_stage`, regardless of what the LLM
  says — this specific safety property **is** code-enforced (dual-layer), and
  is the strongest grounding guarantee in the system today.
- With an empty Qdrant collection (no documents ingested yet, the current
  local-dev state), every retrieval-backed node will correctly return
  `insufficient_evidence: true` / empty citations — verified above via a live
  `/analyze` call reaching the pipeline (it failed earlier at the HF auth
  step, before evaluating evidence, since no HF token is configured yet).
- **Gap for later**: add a code-level check that rejects/flags any diagnosis
  candidate whose `citations` list is empty, independent of the LLM's own
  `insufficient_evidence` flag — this would make strict grounding mode a
  code guarantee instead of a prompt instruction.

## What was NOT carried over from the previous implementation

The previous `app/embeddings`, `app/generation`, `app/prompting`,
`app/retrieval`, and `app/textbook_qa` modules (OpenAI/Gemini-based, 1536-dim
embeddings) are **not** part of this architecture — they used a different
embedding provider and vector dimensionality than Om's HF/384-dim + sparse
BM25 Qdrant schema, so mixing them into one collection would silently corrupt
retrieval. They remain fully intact on `backup/pre-om-ai-service` and in the
`wip(ai): preserve in-progress...` commit. See the integration report for the
full retained/replaced/removed breakdown.
