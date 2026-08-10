# Postman Testing Guide — Exobios AI Service

Base URL: `http://localhost:8000`
Do **not** point Postman (or anything) at the Spring Boot backend for this —
these requests go directly to the FastAPI service.

Only two real endpoints exist: `GET /health` and `POST /analyze`. (There is
no document-upload, retrieval-only, or chat endpoint in this implementation —
ingestion happens offline via the separate `ingestion/` CLI tool, not through
the API.)

## 1. Health check

```
GET http://localhost:8000/health
```
No headers required.

**Expected response — 200:**
```json
{"status": "UP", "service": "exobios-ai-app", "version": "0.1.0"}
```

## 2. Swagger UI (sanity check, not a Postman request)

Open http://localhost:8000/docs in a browser to see the live OpenAPI schema
and try requests interactively before scripting them in Postman.

## 3. Auth checks on /analyze

**3a. Missing API key — expect 401/422**
```
POST http://localhost:8000/analyze
Content-Type: application/json

{}
```
Response: `422` — FastAPI reports both the missing `x-api-key` header and the
missing required body fields (`assessmentId`, `patientId`) in one response.

**3b. Wrong API key — expect 401**
```
POST http://localhost:8000/analyze
Content-Type: application/json
X-Api-Key: wrong-key

{"assessmentId": "11111111-1111-1111-1111-111111111111", "patientId": "22222222-2222-2222-2222-222222222222"}
```
Response:
```json
{"error_code": "authentication_failed", "message": "invalid X-Api-Key"}
```

**3c. Correct API key** — use the value of `AI_API_KEY` in `app/.env`
(defaults to `local-dev-api-key` in this setup).

## 4. Full /analyze request (synthetic patient — do not use real patient data)

```
POST http://localhost:8000/analyze
Content-Type: application/json
X-Api-Key: local-dev-api-key
```

Body:
```json
{
  "assessmentId": "11111111-1111-1111-1111-111111111111",
  "patientId": "22222222-2222-2222-2222-222222222222",
  "patientComplaint": "high fever and cough for 3 days",
  "complaintCategory": "RESPIRATORY",
  "symptoms": [
    {"name": "fever", "duration": "3 days", "severity": "moderate"},
    {"name": "cough", "duration": "2 days", "severity": "mild"}
  ],
  "vitals": {
    "heartRate": 110,
    "spo2": 94,
    "temperature": 39.2,
    "bloodPressureSystolic": 118,
    "bloodPressureDiastolic": 76,
    "respiratoryRate": 22
  },
  "pastIllnesses": "asthma",
  "currentMedications": "salbutamol inhaler",
  "allergies": "none known",
  "age": 34,
  "gender": "male"
}
```

**Verified behavior right now (no Hugging Face / Groq keys configured yet):**
```json
{"error_code": "retrieval_failed", "message": "embedding request failed: 401 Client Error: Unauthorized for url: https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"}
```
HTTP 502. This confirms the pipeline runs end-to-end up to the first external
call — `rule_engine` (pure Python) already ran successfully before this
error. **BLOCKED — USER CREDENTIAL REQUIRED**: add real values for
`EMBEDDING__HF_TOKEN`, `RERANKER__HF_TOKEN`, and `LLM__GROQ_API_KEY` in
`app/.env`, restart the service, and re-run this request.

**Expected response once credentials are configured** (shape, from
`app/schemas/response.py`) — with an empty Qdrant collection, expect
`insufficient_evidence: true` and empty candidate lists, since no documents
have been ingested yet:
```json
{
  "assessment_id": "11111111-1111-1111-1111-111111111111",
  "status": "COMPLETED",
  "deterministic_flags": {
    "flags": [{"code": "...", "severity": "...", "value": 94, "threshold": "..."}],
    "risk_floor": "MEDIUM"
  },
  "diagnosis": {"candidates": [], "query_used": "...", "insufficient_evidence": true},
  "investigation": {"tests": [], "based_on_diagnosis": []},
  "treatment_protocol": {"steps": [], "based_on_diagnosis": [], "patient_factors_considered": [], "regimen_specificity_flag": false},
  "plan_of_action": {"immediate_measures": [], "warning_signs": [], "risk_level": "MEDIUM", "risk_floor_conflict": false, "referral_advice": null},
  "validation_flags": []
}
```

## 5. Representative end-to-end workflow (Step 20)

```
health                              -> confirm service is up
   v
ensure Qdrant has documents          -> currently empty; run ingestion/ separately
   v                                    to populate (see docs/ARCHITECTURE.md);
   v                                    until then, expect insufficient_evidence
POST /analyze (synthetic patient)
   v
inspect deterministic_flags          -> confirm vitals thresholds fired correctly
   v                                    (e.g. spo2=94 -> a flag, not silently ignored)
inspect diagnosis.insufficient_evidence
   v                                    -> true with empty corpus (expected/correct
   v                                       grounding behavior, not a bug)
inspect plan_of_action.risk_level
   v                                    -> must be >= deterministic_flags.risk_floor
   v                                       (code-enforced; check risk_floor_conflict)
check MongoDB (`assessments` collection) -> one doc per assessment_id, upserted
                                             after each stage
```

Ran once with credentials configured but before any ingestion has happened:
expect a `COMPLETED` response with real deterministic flags but empty/
`insufficient_evidence` diagnosis — this demonstrates the grounding safeguard
is working (the model isn't inventing a diagnosis from nothing) rather than
indicating a bug.

## 6. What is intentionally NOT testable yet

- No document upload/ingestion HTTP endpoint exists — ingestion is a separate
  offline CLI (`ingestion/`), not part of this API surface.
- No GET-by-assessment-id endpoint exists yet, even though
  `repositories/assesment.py::get_assessment` is implemented — it's just
  never wired to a route. Query Mongo directly if you need to inspect a
  persisted assessment during testing.
