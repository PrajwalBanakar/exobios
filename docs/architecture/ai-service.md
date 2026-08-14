# AI service architecture

`exobios-ai` is a standalone FastAPI microservice, separate from
`exobios-backend`'s Postgres/Spring stack. It has its own dependencies —
Qdrant (hybrid vector search), MongoDB (assessment persistence), Hugging
Face (embeddings/reranking), and Groq (LLM generation) — none of which the
backend talks to directly.

> This document originally described the AI-1 placeholder phase (no
> clinical logic, `/analyze` always returned a fixed stub). That phase ended
> when a LangGraph-based clinical pipeline replaced the stub; this document
> now describes the current architecture. See the 2026-08 production-
> readiness audit for the full history, including a contract-shape bug that
> existed for a period between the two phases.

## Call flow

```text
Client
  └─ POST /assessments/{id}/submit  (Spring Boot backend)
        └─ AssessmentService.submitAssessment
              └─ RestAiGateway.analyzeAssessment(AiRequest)   [synchronous, blocking]
                    └─ POST http://ai-service:8000/analyze    (X-Api-Key header)
                          └─ exobios-ai: verify key → validate AiRequest
                                → rule_engine → diagnosis → investigation
                                → treatment_protocol → plan_of_action
                                → return AiResponse-compatible AssessmentResponse
              └─ persists AiAssessmentResult, mirrors riskLevel onto Assessment
```

The call is synchronous and sits inside the same HTTP request/DB transaction
as assessment submission — see `docs/api/ai-service-contract.md` for the
timeout/retry/fallback behavior and response shape. If the AI service is
unreachable or errors, `RestAiGateway` (and, as a second safety net,
`AssessmentService` itself) falls back to `AiResponse.placeholder()`, now
with `status=FAILED` (not `PENDING` — see the contract doc); assessment
submission never fails outright because the AI service is down, but the
failure is recorded honestly rather than presented as a real result.

Nothing in the backend currently calls `AiGateway.health()` — it exists on
the interface but has no caller yet (likely intended for a future actuator
health indicator). `exobios-ai` also exposes `GET /health/ready`, which
actually checks Mongo/Qdrant connectivity — not part of this contract today
but available for that future use.

## Pipeline

`exobios-ai/app/graph/builder.py` runs a linear LangGraph pipeline:
deterministic vitals-threshold rules (no LLM/retrieval) → diagnosis
(hybrid Qdrant retrieval + reranking + Groq, grounded and citation-verified)
→ investigation → treatment protocol → plan of action (synthesizes prior
stages; risk level is force-clamped in code to the deterministic risk
floor). Every stage's output is persisted to MongoDB. See
`exobios-ai/docs/ARCHITECTURE.md` for the full pipeline detail and grounding
safeguards.

## Boundaries / what's out of scope

`exobios-ai` never invents clinical thresholds or rules — the deterministic
rule engine's vitals thresholds are explicitly documented in its own source
as placeholder values pending clinical review, not a substitute for
client-supplied/clinically-reviewed thresholds. Ingestion (populating the
Qdrant corpus from source documents) is a separate offline project
(`exobios-ai/ingestion/`), not part of this service's runtime.
