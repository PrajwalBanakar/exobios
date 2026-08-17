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
  when evidence is thin — this remains prompt-guidance, but it is no longer
  the only safeguard (see below).
- **Now code-enforced** (production-readiness audit, 2026-08-14):
  `validate_stage` (`app/graph/nodes/validation.py`) cross-checks every
  citation an LLM stage returns against `AssessmentState.retrieved_evidence`
  — the literal chunks retrieved for that stage. A citation whose `chunk_id`
  wasn't retrieved is dropped rather than trusted (and, for a citation that
  *does* match, the excerpt text is replaced with the authoritative
  retrieved text rather than the LLM's own transcription of it). Any
  diagnosis candidate / investigation test / treatment step left with zero
  verified citations is dropped. If diagnosis ends up with no verified
  candidates, `insufficient_evidence` is force-set to `True` in code,
  independent of the LLM's own flag. Diagnosis also skips the LLM call
  entirely when retrieval returns nothing, returning
  `insufficient_evidence=True` directly — an empty knowledge base can no
  longer reach the point of the model reasoning from its own training data.
  Unit tests: `tests/test_citation_verification.py`.
- The other code-enforced safeguard is the deterministic risk floor:
  `rule_engine`'s vitals thresholds are re-checked and force-overridden in
  code in both `plan_of_action_node` and `validate_stage`, regardless of
  what the LLM says.
- **Not yet code-enforced**: exact-text groundedness beyond the chunk_id
  match (an LLM could still cite a real, retrieved chunk_id in support of a
  claim the chunk doesn't actually substantiate — verification confirms the
  citation is a real retrieved excerpt, not that the excerpt logically
  supports the specific claim attached to it). Judging that would need an
  entailment/NLI check or a second LLM pass, out of scope for this round.
- **Verified live** (2026-08-10, real credentials, real corpus): with
  `Biochemistry.pdf` ingested (2,853 chunks, a general biochemistry
  textbook — not a clinical guideline), a `/analyze` call for "high fever
  and cough for 3 days" correctly returned `insufficient_evidence: true`
  with empty candidates. Direct inspection of `retrieve_and_rerank()`'s
  output for that same query confirmed retrieval genuinely ran (Qdrant
  hybrid search returned topically-adjacent excerpts — a case study
  mentioning fever, a list of viral respiratory diseases) but the LLM
  correctly judged none of it as actual diagnostic evidence and declined to
  fabricate a diagnosis. This is the grounding safeguard working as
  designed, not a retrieval failure.
- **Reranker: investigated 2026-08-14, no fix applied — needs an owner
  decision.** The configured model, `cross-encoder/ms-marco-MiniLM-L-6-v2`,
  returns `400: "Model not supported by provider hf-inference"` (verified
  live). Checked whether a different HF-hosted cross-encoder/text-ranking
  model would work instead: querying HF's own model-listing API for
  `pipeline_tag=text-ranking` with `inference_provider=all` returns **zero
  models with any active hosted-inference provider** — this is not specific
  to this one model, HF's Inference Providers network currently has no
  serving option for cross-encoder reranking at all, on any model. Per the
  audit's own instruction not to randomly swap in an unverified
  model/provider, no code change was made to the model/URL. Instead:
  `RERANKER__ENABLED` (default `true`, set to `false` in this project's
  `.env`/`.env.example`) now skips the HTTP call entirely rather than
  paying a guaranteed-400 round trip on every retrieval call;
  `reranker_service.py`'s try/except fallback (unchanged, already correct)
  still returns the original RRF-fused order rather than crashing retrieval
  if it's ever re-enabled against a still-broken endpoint; `/health/ready`
  now reports the reranker's enabled/disabled state so this is observable
  in production, not silent. Options for the actual owner decision, in
  rough order of effort:
    1. **Leave disabled** (current state) until real evaluation data exists
       to show reranking would measurably improve results for this corpus —
       ties into the not-yet-built RAG evaluation framework.
    2. **Self-host a small cross-encoder** (e.g. the same
       `cross-encoder/ms-marco-MiniLM-L-6-v2`, ~80MB, via the
       `sentence-transformers` `CrossEncoder` class run in-process). Removes
       the HF-hosted-inference dependency for this one step entirely, at the
       cost of CPU and deploy size — but contradicts this service's stated
       "API call, not local inference" constraint (`reranker_service.py`'s
       original docstring), so needs an explicit decision to relax that
       constraint, not just a model swap.
    3. **A different, paid reranking API** (e.g. Cohere Rerank, Jina
       Reranker, Voyage AI rerank) — introduces a new paid vendor and, for a
       healthcare system, a new data-sharing/BAA question that needs
       business sign-off, not an engineering judgment call.
  Not implemented: a bi-encoder cosine-similarity "pseudo-rerank" using the
  already-working embedding endpoint was considered and deliberately not
  built — it would be largely redundant with the dense leg of hybrid search
  (same model, same vector space) and its value is unverifiable without the
  same evaluation data option 1 is waiting on.
- **Closed**: the code-level citation-verification check described above
  (previously listed here as a future gap) is implemented as of the
  2026-08-14 production-readiness pass.

## What was NOT carried over from the previous implementation

The previous `app/embeddings`, `app/generation`, `app/prompting`,
`app/retrieval`, and `app/textbook_qa` modules (OpenAI/Gemini-based, 1536-dim
embeddings) are **not** part of this architecture — they used a different
embedding provider and vector dimensionality than Om's HF/384-dim + sparse
BM25 Qdrant schema, so mixing them into one collection would silently corrupt
retrieval. They remain fully intact on `backup/pre-om-ai-service` and in the
`wip(ai): preserve in-progress...` commit. See the integration report for the
full retained/replaced/removed breakdown.
