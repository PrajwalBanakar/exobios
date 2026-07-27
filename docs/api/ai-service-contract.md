# AI service contract (AI-1)

The contract between `exobios-backend`'s `RestAiGateway` and the `exobios-ai`
FastAPI service. Source of truth is the Java code in
`exobios-backend/src/main/java/com/exobios/backend/integration/ai/` and
`exobios-backend/src/main/java/com/exobios/backend/assessments/entity/enums/`
— this document mirrors it and must be kept in sync if either side changes.

## Transport

- Base URL: `app.ai.base-url` / env `AI_SERVICE_URL` (default `http://localhost:8000`).
- Every request carries `X-Api-Key: <app.ai.api-key>` (env `AI_API_KEY`).
- `POST /analyze`: connect timeout 5s, read timeout 30s, up to 2 retries (3
  attempts total) on any `RestClientException`; falls back to
  `AiResponse.placeholder()` if all attempts fail.
- `GET /health`: no retry; any 2xx response ⇒ healthy, any exception
  (connection failure, timeout, non-2xx) ⇒ unhealthy. Response body is not
  inspected by the Java client.

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

| Field | Type | Nullable |
|---|---|---|
| `heartRate` | integer | yes |
| `spo2` | decimal | yes |
| `temperature` | decimal | yes |
| `bloodPressureSystolic` | integer | yes |
| `bloodPressureDiastolic` | integer | yes |
| `respiratoryRate` | integer | yes |

`ComplaintCategory` enum literals: `FEVER`, `RESPIRATORY`, `GASTROINTESTINAL`,
`MATERNAL_HEALTH`, `CHILD_HEALTH`, `SKIN`, `MUSCULOSKELETAL`, `NEUROLOGICAL`,
`CARDIOVASCULAR`, `MENTAL_HEALTH`, `OTHER`.

## `POST /analyze` response (`AiResponse`)

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `status` | enum `AiResultStatus` | no | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED` |
| `summary` | string | yes | |
| `riskLevel` | enum `RiskLevel` | yes | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` — nullable end-to-end (DTO, entity, DB `CHECK (risk_level IS NULL OR risk_level IN (...))`) |
| `confidenceScore` | number | yes | Java `BigDecimal`, DB `NUMERIC(5,4)`. **Must serialize as a JSON number, not a string** — this is why the Python schema uses `float` rather than `Decimal` (Pydantic v2 serializes `Decimal` as a JSON string by default, which a Java `BigDecimal` field would not parse). |
| `redFlags` | string | yes | |
| `recommendations` | string | yes | |
| `modelVersion` | string | yes | |
| `source` | string | yes | |

`processingTimeMs` and `generatedAt` are **not** part of this contract — the
backend computes/stamps those itself in `AssessmentService`, never reading
them from the AI response.

## AI-1 stub response

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

`riskLevel: null` is a deliberate choice, not an oversight: `RiskLevel` is
nullable at every layer (DTO, JPA entity, both `risk_level` DB columns, and
their `CHECK` constraints all explicitly permit `NULL`). Returning `LOW`
instead would falsely claim a patient was clinically triaged as low risk,
which AI-1 must never do. `status: PENDING` matches the same value Java's own
`AiResponse.placeholder()` uses for "no real analysis has happened yet."

## `GET /health` response

```json
{"status": "UP", "service": "exobios-ai", "version": "0.1.0"}
```

No API key required. The Java client only checks HTTP status, so this shape
is for humans/tooling, not a contract Java parses.
