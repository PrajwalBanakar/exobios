# AI service contract

The contract between `exobios-backend`'s `RestAiGateway` and the `exobios-ai`
FastAPI service. Source of truth is the Java code in
`exobios-backend/src/main/java/com/exobios/backend/integration/ai/` and
`exobios-backend/src/main/java/com/exobios/backend/assessments/entity/enums/`,
and the Python code in `exobios-ai/app/schemas/request.py` and
`response.py` — this document mirrors both and must be kept in sync if
either side changes.

> **History**: this document originally described the AI-1 placeholder
> phase, where `/analyze` always returned a fixed stub response. That phase
> ended when a LangGraph-based clinical pipeline replaced the stub, but this
> document — and the wire contract it describes — were not updated at the
> same time, which left `RestAiGateway` and `/analyze` returning
> incompatible JSON shapes for a period (a snake_case, deeply nested
> response colliding with a DTO expecting flat camelCase fields). That gap
> is what the 2026-08 Priority 1 fix below closes.

## Transport

- Base URL: `app.ai.base-url` / env `AI_SERVICE_URL` (default `http://localhost:8000`).
- Every request carries `X-Api-Key: <app.ai.api-key>` (env `AI_API_KEY`).
- `POST /analyze`: connect timeout 5s, read timeout 30s, up to 2 retries (3
  attempts total) on any `RestClientException`; falls back to
  `AiResponse.placeholder()` if all attempts fail.
- `GET /health`: no retry; any 2xx response ⇒ healthy, any exception
  (connection failure, timeout, non-2xx) ⇒ unhealthy. Response body is not
  inspected by the Java client.
- `GET /health/ready`: not currently called by the backend (nothing consumes
  `AiGateway.health()` beyond a manual check either — see
  `docs/architecture/ai-service.md`). Intended for a future orchestrator
  readiness probe, not part of this contract.

## `POST /analyze` request (`AiRequest`)

camelCase JSON, no custom Jackson naming. Null fields are omitted by the
backend (`spring.jackson.default-property-inclusion: non_null`), so every
optional field may be entirely absent, not just `null`.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `assessmentId` | UUID | no | |
| `patientId` | UUID | no | |
| `patientComplaint` | string | yes | |
| `complaintCategory` | enum `ComplaintCategory` | yes | see below |
| `symptoms` | array of `{name, duration, severity}` | `[]` when none | `name` required, `duration`/`severity` nullable strings |
| `vitals` | object | yes | see below |
| `pastIllnesses` | string | yes | |
| `currentMedications` | string | yes | |
| `allergies` | string | yes | |

`vitals` object:

| Field | Type | Nullable | Unit / bound |
|---|---|---|---|
| `heartRate` | integer | yes | bpm |
| `spo2` | decimal | yes | % |
| `temperature` | decimal | yes | **Fahrenheit.** Validated 86.0–113.0 identically on both the backend (`VitalsRequest.temperature`) and the AI service (`schemas/request.py::VitalsSummary.temperature`) — see "Temperature unit" below. |
| `bloodPressureSystolic` | integer | yes | mmHg |
| `bloodPressureDiastolic` | integer | yes | mmHg |
| `respiratoryRate` | integer | yes | breaths/min |

`ComplaintCategory` enum literals: `FEVER`, `RESPIRATORY`, `GASTROINTESTINAL`,
`MATERNAL_HEALTH`, `CHILD_HEALTH`, `SKIN`, `MUSCULOSKELETAL`, `NEUROLOGICAL`,
`CARDIOVASCULAR`, `MENTAL_HEALTH`, `OTHER`.

### Temperature unit (fixed 2026-08, Priority 2)

`vitals.temperature` is **Fahrenheit** end to end:

```text
Frontend (NewAssessmentView.vue, DeviceView.vue — labeled "(°F)" throughout)
  → Spring Boot VitalsRequest.temperature   [86.0–113.0, was wrongly 30.0–45.0 "°C"]
  → Vitals entity / VitalsDto                [documented Fahrenheit in a comment]
  → AiRequest.VitalsSummary.temperature      [BigDecimal, no conversion]
  → exobios-ai schemas/request.py            [86–113, was a wider AI-only 60–115]
  → rule_engine.py thresholds                [104 HYPERPYREXIA / 102 HIGH_FEVER — Fahrenheit]
```

Before the fix, `VitalsRequest.temperature` validated as Celsius
(30.0–45.0) while the frontend collected and the AI rule engine interpreted
Fahrenheit — a real Fahrenheit reading like 100.8 would have been rejected
by backend validation before ever reaching the AI service. The bound is now
86.0–113.0°F on both the backend and the AI service (a physiological
plausibility range, not a clinical threshold — it is the mathematical
Fahrenheit conversion of the original, mistaken 30–45°C bound). The rule
engine's actual clinical thresholds (104/102) were **not** changed.

## `POST /analyze` response (`AiResponse`)

### Legacy-compatible top-level fields (fixed 2026-08, Priority 1)

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `status` | enum `AiResultStatus` | no | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`. exobios-ai always returns `COMPLETED` on a successful pipeline run (including when `insufficientEvidence` is true — that's a legitimate completed outcome, not a failure). `PENDING`/`PROCESSING` are never returned by exobios-ai (the call is synchronous); the backend uses `FAILED` for its own gateway-failure fallback. |
| `summary` | string | yes | Mechanically derived from the real pipeline state (top diagnosis candidate + risk level, or an explicit insufficient-evidence statement) — never LLM-generated specifically for this field, never fabricated. |
| `riskLevel` | enum `RiskLevel` | yes | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. Equals `planOfAction.riskLevel`, which is force-clamped in code to the deterministic `riskFloor` — the LLM cannot lower it. |
| `confidenceScore` | number | yes | Java `BigDecimal`, DB `NUMERIC(5,4)`. Top diagnosis candidate's confidence, or `null` when there are no candidates (never defaulted to `0.0` or fabricated). **Must serialize as a JSON number, not a string** — the Python schema uses `float` rather than `Decimal` for exactly this reason. |
| `redFlags` | string | yes | Deterministic flag codes + detected warning signs + a risk-floor-override note, joined with `; `. Empty string when none. |
| `recommendations` | string | yes | Ordered immediate measures + referral advice, joined with `; `. |
| `modelVersion` | string | yes | The configured Groq model (e.g. `llama-3.3-70b-versatile`), not a hardcoded version string. |
| `source` | string | yes | `"exobios-ai-langgraph"` on success; `"exobios-ai-unavailable"` on the backend's own gateway-failure placeholder. |

### Full structured detail (additive, ignored by the current backend)

The response also includes the complete per-stage pipeline output —
`deterministicFlags`, `diagnosis` (candidates with citations), `investigation`,
`treatmentProtocol`, `planOfAction`, `validationFlags` — all camelCase. The
backend's Jackson config (`fail-on-unknown-properties: false`) ignores these
today without erroring; they exist for any future consumer (an enriched
`AiResponse`/`AiAssessmentResult`, a different frontend view) that wants
more than the seven summary fields above, without requiring another
contract change to add them. See `exobios-ai/app/schemas/response.py`'s
docstring and `exobios-ai/tests/test_analyze.py` for the exact current shape.

`processingTimeMs` and `generatedAt` are **not** part of this contract — the
backend computes/stamps those itself in `AssessmentService`, never reading
them from the AI response.

### The bug this replaced

Before this fix, `/analyze` returned a snake_case body
(`assessment_id`, `deterministic_flags`, `diagnosis`, …) with none of
`AiResponse`'s fields present at the top level. Spring's Jackson
(`fail-on-unknown-properties: false`) did **not** throw on this — it
silently built an `AiResponse` with `status=COMPLETED` (the one field name
that happened to coincide) and every clinical field (`summary`, `riskLevel`,
`confidenceScore`, `redFlags`, `recommendations`) `null`. That is worse than
an exception: `RestAiGateway`'s retry/placeholder fallback only triggers on
a *thrown* exception, so a real, richly-grounded AI result would have
reached `AssessmentService` looking like a successful-but-empty analysis,
indistinguishable from "the AI ran and found nothing." This is empirically
verified (not just reasoned about) in
`exobios-backend/src/test/java/.../integration/ai/AiResponseContractTest.java`.

### Failure fallback (`AiResponse.placeholder()`, fixed 2026-08)

Returned when the AI gateway could not produce a real result (network
failure, non-2xx, or an exception in `AssessmentService.callAiGateway`).
Status is **`FAILED`**, not `PENDING` — `submitAssessment` calls the gateway
synchronously, so there is no later async moment this could still resolve
in; claiming `PENDING` implied a retry that would never happen.
`riskLevel`/`confidenceScore`/`redFlags` are `null`/empty, never defaulted
to anything a reader could mistake for a real clinical judgment (e.g. never
`LOW` risk):

```json
{
  "status": "FAILED",
  "summary": "AI analysis could not be completed — the AI service was unavailable or returned an error",
  "riskLevel": null,
  "confidenceScore": null,
  "redFlags": null,
  "recommendations": "Assessment should be reviewed manually; AI analysis did not run",
  "modelVersion": "unavailable",
  "source": "exobios-ai-unavailable"
}
```

## Example real `/analyze` response (sanitized)

```json
{
  "assessmentId": "3f2a1c9e-1234-4a5b-8c6d-9e0f1a2b3c4d",
  "status": "COMPLETED",
  "summary": "Top differential: Dengue Fever (HIGH confidence). Risk level: HIGH. 2 candidate(s) considered.",
  "riskLevel": "HIGH",
  "confidenceScore": 0.82,
  "redFlags": "SPO2_LOW (90-93%)",
  "recommendations": "Administer ORS; Monitor platelet count; Refer if warning signs develop",
  "modelVersion": "llama-3.3-70b-versatile",
  "source": "exobios-ai-langgraph",
  "deterministicFlags": { "flags": [{"code": "SPO2_LOW", "severity": "HIGH", "value": 92, "threshold": "90-93%"}], "riskFloor": "HIGH" },
  "diagnosis": { "candidates": [{"diseaseName": "Dengue Fever", "confidenceScore": 0.82, "confidenceLabel": "HIGH", "citations": [{"chunkId": "...", "documentId": "...", "excerpt": "...", "heading": "Dengue", "page": 12}], "reasoning": "..."}], "queryUsed": "...", "insufficientEvidence": false },
  "investigation": { "tests": [...], "basedOnDiagnosis": ["Dengue Fever"] },
  "treatmentProtocol": { "steps": [...], "basedOnDiagnosis": ["Dengue Fever"], "patientFactorsConsidered": [], "regimenSpecificityFlag": false },
  "planOfAction": { "immediateMeasures": [...], "warningSigns": [...], "riskLevel": "HIGH", "riskFloorConflict": false, "referralAdvice": "..." },
  "validationFlags": []
}
```

## `GET /health` response

```json
{"status": "UP", "service": "exobios-ai", "version": "0.1.0"}
```

No API key required. The Java client only checks HTTP status, so this shape
is for humans/tooling, not a contract Java parses.
