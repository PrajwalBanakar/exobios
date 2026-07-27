# AI service architecture (AI-1)

`exobios-ai` is a standalone FastAPI microservice, separate from
`exobios-backend`'s Postgres/Spring stack. In AI-1 it has no datastore of its
own and no external dependencies — it is a pure request/response service.

## Call flow

```text
Client
  └─ POST /assessments/{id}/submit  (Spring Boot backend)
        └─ AssessmentService.submitAssessment
              └─ RestAiGateway.analyzeAssessment(AiRequest)   [synchronous, blocking]
                    └─ POST http://ai-service:8000/analyze    (X-Api-Key header)
                          └─ exobios-ai: verify key → validate AiRequest → return AiResponse
              └─ persists AiAssessmentResult, mirrors riskLevel onto Assessment
```

The call is synchronous and sits inside the same HTTP request/DB transaction
as assessment submission — see `docs/api/ai-service-contract.md` for the
timeout/retry/fallback behavior. If the AI service is unreachable or errors,
`RestAiGateway` (and, as a second safety net, `AssessmentService` itself)
falls back to `AiResponse.placeholder()`; assessment submission never fails
because the AI service is down.

Nothing in the backend currently calls `AiGateway.health()` — it exists on
the interface but has no caller yet (likely intended for a future actuator
health indicator).

## AI-1 boundaries

This phase intentionally implements no clinical logic: no RAG, no vector
store, no LLM, no rules engine. `/analyze` always returns the same
placeholder response (see the contract doc). This keeps the integration
(auth, schemas, error handling, Docker/Compose wiring) provable before any
clinical functionality is added in a later phase.
