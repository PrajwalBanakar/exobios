# Exobios — AI-Assisted Healthcare Platform

Exobios is a field-health platform built for India's community health worker network
(ASHA, ANM, CHO, LHV, Health Assistants) and MBBS Doctors. A health worker registers a
patient, walks through a structured symptom/history/examination intake, and gets an
AI-assisted differential diagnosis and a role-aware plan of action (referral, ambulance,
or teleconsultation). Assessments that need escalation flow into a doctor-facing
referral-review queue.

This repository is a monorepo with three parts:

| Folder | Status | Description |
|---|---|---|
| `exobios-frontend/` | **Active** | Vue 3 PWA. Functionally complete against mock/local data — every role (ASHA/ANM/CHO/LHV/Health Assistant, MBBS Doctor, Super Admin) is implemented end to end. Not yet wired to the live backend. |
| `exobios-backend/` | **Active** | Spring Boot API (Java 21). 20+ domain modules covering auth, patients, assessments, clinical decision support, referrals, doctor review, devices, SOS, notifications, feedback, analytics, and audit — with a full Testcontainers-backed test suite. Calls `exobios-ai` synchronously on assessment submit; not yet integrated with the frontend. |
| `exobios-ai/` | **Active** | FastAPI + LangGraph RAG service — grounded clinical diagnosis/investigation/treatment/plan-of-action pipeline over a Qdrant corpus, called by the backend's `AiGateway`. Own CI (lint + test + docker build), retry/rate-limiting, and a mocked test suite. See [AI integration](#ai-integration--exobios-ai) below and [`exobios-ai/README.md`](exobios-ai/README.md) for the full pipeline/setup docs. |

**Frontend and backend are each independently functional but not yet connected to each
other.** The frontend runs entirely on mock data seeded into `localStorage`, by design,
so it can be developed and demoed without a live API. The backend exposes a complete
REST API of its own, integrates with the real `exobios-ai` service, and can be run and
tested in isolation via Postman/Swagger. Wiring the frontend to the backend is the next
major milestone — see [Known limitations](#known-limitations).

```
                     ┌───────────────────┐        (not yet wired)        ┌──────────────────────┐
   ASHA / Doctor ───▶│  exobios-frontend │╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌▶│   exobios-backend     │
   / Admin            │  Vue 3 PWA        │        REST + JWT             │   Spring Boot API     │
                     └───────────────────┘                               └──────────┬────────────┘
                                                                                      │ POST /analyze
                                                                                      │ X-Api-Key
                                                                                      ▼
                                                                          ┌──────────────────────┐
                                                                          │   exobios-ai         │
                                                                          │   FastAPI + LangGraph│
                                                                          │   RAG pipeline       │
                                                                          └──────────────────────┘
```

---

## Role model

Every account resolves to one role, which drives what the UI/API surfaces:

| Role | Who | Capability |
|---|---|---|
| `ASHA` | ASHA / ANM / CHO / LHV / Health Assistant | Register patients, run assessments, view AI-assisted results, initiate referrals/SOS |
| `DOCTOR` | MBBS Doctor | Referral-review queue (assign → under review → action taken → closed), clinical notes, teleconsult |
| `SUPER_ADMIN` | Platform admin | User/device management, analytics dashboard, audit log |

---

## `exobios-backend`

Spring Boot 3.3 / Java 21 REST API. PostgreSQL via Flyway-managed migrations, JWT auth,
role-based access control, and an AOP-based audit trail on every write.

### Tech stack

- **Spring Boot 3.3** — Web, Data JPA, Security, Validation, Actuator, AOP
- **PostgreSQL** + **Flyway** — versioned schema migrations (`V1`…`V10`)
- **JJWT** — access/refresh token auth
- **MapStruct** + **Lombok** — entity ↔ DTO mapping
- **springdoc-openapi** — Swagger UI generated from the live API
- **JUnit 5**, **Spring Security Test**, **Testcontainers** (Postgres) — unit, web-layer, and real-database integration tests

### Module map

| Module | Responsibility |
|---|---|
| `auth` | Login, JWT issue/refresh |
| `users` | User CRUD, role assignment |
| `patients` | Patient registry |
| `assessments` | Symptom/vitals/history intake, submission, AI-result persistence |
| `integration/ai` | `AiGateway` — the HTTP contract (`POST /analyze`, `GET /health`) to the external AI service; retries, timeouts, and a graceful `PENDING` fallback when it's unreachable |
| `measures` | Immediate actions/interventions taken on an assessment |
| `referrals` | Referral lifecycle + doctor review/assignment/clinical-notes workflow |
| `doctor` | Doctor dashboard (assigned/under-review/action-taken/closed counts) |
| `devices` | Field device registry (pulse oximeters, BP monitors, etc.) and assignment |
| `sos` | Emergency/SOS record capture |
| `notifications` | In-app notifications |
| `feedback` | User feedback capture + admin response |
| `analytics` | Dashboard aggregates — risk summary, referral summary, village/ASHA performance |
| `audit` | `@Auditable`-annotated write operations logged immutably (`audit_logs`) |
| `common` | Shared DTOs, exceptions, pagination, base entity |
| `config`, `security` | CORS, Spring Security filter chain, JWT filter, `UserPrincipal` |
| `events`, `scheduler`, `sync`, `storage`, `logging` | Supporting infrastructure |

### AI integration — `exobios-ai`

- On `POST /assessments/{id}/submit`, `AssessmentService` synchronously calls
  `AiGateway.analyzeAssessment(...)`, which posts the assessment (complaint, symptoms,
  vitals, history) to `${AI_SERVICE_URL}/analyze` with an `X-Api-Key` header.
- Response (`risk level`, `summary`, `red flags`, `recommendations`, `confidence`) is
  persisted 1:1 against the assessment and mirrored onto `assessments.risk_level` for
  analytics.
- If the AI service is unreachable or exhausts 2 retries, the gateway falls back to a
  `FAILED`-status placeholder result rather than failing the request or fabricating a
  clinical judgment.
- `exobios-ai/` implements this service: a FastAPI app running a 5-stage LangGraph
  pipeline (deterministic rule engine → diagnosis → investigation → treatment protocol →
  plan of action) grounded via hybrid (dense + BM25) retrieval over a Qdrant corpus of
  approved clinical protocols (IMNCI/national CHW guidelines), with every LLM-cited
  finding cross-checked against what was actually retrieved before it's trusted —
  ungrounded findings are dropped, and an empty/insufficient retrieval result short-
  circuits straight to `insufficient_evidence` rather than letting the model
  free-associate. A separate `ingestion/` pipeline populates that Qdrant corpus from
  source documents (PDF/DOCX → parse → classify → chunk → embed → upsert), and the
  service persists per-stage state to MongoDB, one document per assessment. Full
  architecture, pipeline detail, and local setup: [`exobios-ai/README.md`](exobios-ai/README.md).
- The service's `/analyze` response is a superset of the flat legacy shape
  `AiGateway`/`AiResponse` deserialize (`status`/`summary`/`riskLevel`/
  `confidenceScore`/`redFlags`/`recommendations`/`modelVersion`/`source`), plus the full
  per-stage detail as additive fields the backend currently ignores
  (`fail-on-unknown-properties: false`) — see
  [`docs/api/ai-service-contract.md`](docs/api/ai-service-contract.md).

### Setup

Requires Java 21, Maven, and Docker (for Postgres).

```bash
cd exobios-backend
docker compose up postgres -d     # starts Postgres on localhost:5432
mvn spring-boot:run                # applies Flyway migrations on boot, starts on :8080
```

Config is environment-driven (see `application.yml`); sane local defaults exist for
everything, so no `.env` is required to get started. Key overrides:

| Variable | Default | Purpose |
|---|---|---|
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | `localhost` / `5432` / `exobios` / `exobios` / `exobios` | PostgreSQL connection |
| `JWT_SECRET` | dev key (⚠️ replace in production) | JWT signing key |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origin(s) |
| `AI_SERVICE_URL` / `AI_API_KEY` | `http://localhost:8000` / `dev-key` | Where the AI gateway calls out to (see above) |
| `STORAGE_TYPE` / `STORAGE_LOCAL_PATH` | `local` / `./uploads` | File storage backend |

Or run the full stack (Postgres + backend) via `docker compose up -d`.

### API docs

Once running: Swagger UI at `http://localhost:8080/swagger-ui.html`, health check at
`http://localhost:8080/actuator/health`.

### Seeded dev accounts

`V2`/`V10` migrations seed one account per role for local testing:

| Role | Phone | Password |
|---|---|---|
| `SUPER_ADMIN` | `9999999999` | `Admin@123` |
| `ASHA` | `9876543210` | `Asha@123` |
| `DOCTOR` | `9876500002` | `Doctor@123` |

### Testing

```bash
mvn test      # unit + web-layer tests
mvn verify    # + Testcontainers-backed repository integration tests (*RepositoryIT)
```

---

## `exobios-ai`

FastAPI service running a grounded, citation-verified clinical RAG pipeline, plus a
separate offline `ingestion/` pipeline that populates the Qdrant corpus it reads from.
Full detail (architecture, environment setup, request/response shape, troubleshooting):
[`exobios-ai/README.md`](exobios-ai/README.md).

### Tech stack

- **FastAPI** + **Pydantic v2** — HTTP layer, config, request/response validation
- **LangGraph** — orchestrates the 5-stage pipeline (deterministic rules → diagnosis →
  investigation → treatment protocol → plan of action); **LangSmith** for optional
  tracing
- **Qdrant** — hybrid vector store (dense + BM25 sparse, RRF fusion)
- **MongoDB** — per-assessment stage persistence
- **Groq** (`llama-3.3-70b-versatile`) — LLM generation; **Hugging Face** hosted
  inference — embeddings + reranking
- **pytest** — full suite mocks every external dependency (Qdrant/Mongo/HF/Groq), so it
  needs no live services to run
- **ruff** — lint, enforced in CI

### Setup

```bash
cd exobios-ai
docker compose up -d          # Qdrant (+ Mongo, if not already running)
cd app
uv sync
cp .env.example .env          # Qdrant, HF, Groq, Mongo keys — see exobios-ai/README.md
uv run uvicorn main:app --reload --port 8000
```

### Testing

```bash
cd exobios-ai
uv run --project app pytest tests/ -v      # app/ — mocked, no live services
cd ingestion && uv run pytest tests/ -v    # ingestion/ — pure-logic, no live services
```

CI (`.github/workflows/exobios-ai.yml`) runs both suites plus `ruff check` and a Docker
build on every push/PR touching `exobios-ai/`.

---

## `exobios-frontend`

Vue 3 PWA. Fully functional against mock/local data — every role's flows are
implemented end to end without requiring a live backend.

### Tech stack

- **Vue 3** (Composition API, `<script setup>`)
- **Vite** — dev server & build
- **Pinia** — state management
- **Vue Router 4**
- **Tailwind CSS**
- **vite-plugin-pwa** — installable PWA (manifest, service worker, offline app shell)
- **Vitest** + **@vue/test-utils** + **@testing-library/vue** — unit tests, with coverage across auth, patients, assessments, stores, and components
- Custom i18n (English / Hindi / Kannada)

### Architecture

Feature-based structure under `exobios-frontend/src/`:

```
features/<domain>/
  views/       route-level pages
  components/  feature-scoped components
  stores/      Pinia store for this domain (if any)
  constants/   feature-scoped constant data
shared/
  components/  reusable UI (AppShell, form primitives, modals, toasts…)
  constants/   cross-feature constants (hospitals, doctors, transport options…)
  stores/      cross-feature Pinia stores (e.g. actionPlan)
  services/    api.js — thin fetch wrapper for the backend (scaffolded, not yet used by any store)
  offline/     offline queue + network-status detection
```

Feature modules: `admin`, `assessments`, `auth`, `dashboard`, `devices`, `doctor`,
`feedback`, `measures`, `notifications`, `patients`, `referrals`, `reports`,
`settings`, `sos`, `teleconsult` — one per role-facing capability, mirroring the
backend's module map above.

Role model: every logged-in user resolves to one `roleCategory` — `PARAMEDIC`
(ASHA/ANM/CHO/LHV/Health Assistant), `DOCTOR` (MBBS Doctor), or `ADMIN` (Super Admin) —
which drives which examination module, plan-of-action options, and teleconsult doctor
tier a user sees.

### Setup

Requires Node.js 18+.

```bash
cd exobios-frontend
npm install
```

### Run (development)

```bash
npm run dev
```

Starts the Vite dev server (defaults to `http://localhost:5173`, or the next free port).
Sign up as any role (ASHA/ANM/CHO/LHV/Health Assistant/MBBS Doctor) from the login
screen — accounts are stored in `localStorage`, no backend required.

### Build (production)

```bash
npm run build      # outputs to exobios-frontend/dist/
npm run preview    # serve the production build locally
```

### Test

```bash
npm run test           # run once
npm run test:watch     # watch mode
npm run test:ui        # Vitest UI
npm run test:coverage  # coverage report
```

---

## Known limitations

- **Frontend and backend are not yet integrated.** The frontend's `shared/services/api.js`
  HTTP client exists (JWT bearer auth, configurable `VITE_API_BASE_URL`) but no store
  currently calls it — patients, referrals, and teleconsult sessions are still
  seeded/mutated entirely in `localStorage`/memory on the frontend, independent of the
  backend's real Postgres-backed API.
- `referrals` and `teleconsult` Pinia stores are in-memory only (reset on full page
  reload); `patients` and `auth` do persist to `localStorage`.
- Frontend AI differential diagnosis, treatment protocols, and investigation
  recommendations are static placeholder content, not the real model — the frontend
  isn't wired to the backend at all yet (see above), so it never reaches the real
  `exobios-ai` pipeline. The backend↔`exobios-ai` integration itself is real and tested
  — see [AI integration](#ai-integration--exobios-ai).
- `exobios-ai`'s retrieval quality depends entirely on what's been ingested into its
  Qdrant corpus. With a small or non-clinical corpus, `/analyze` correctly returns
  `insufficient_evidence: true` rather than a fabricated diagnosis — see
  [`exobios-ai/README.md`](exobios-ai/README.md) for current corpus status.
- Frontend reports page is static demo data, not derived from the patient/assessment
  stores.
- AI-assisted results on the backend are computed **synchronously** inside the
  assessment-submit request — there's no async/queue path yet, so a slow or unreachable
  AI service directly extends submit latency (mitigated today by the retry/timeout/
  placeholder-fallback behavior in `AiGateway`).
