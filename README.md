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
| `exobios-backend/` | **Active** | Spring Boot API (Java 21). 20+ domain modules covering auth, patients, assessments, clinical decision support, referrals, doctor review, devices, SOS, notifications, feedback, analytics, and audit — with a full Testcontainers-backed test suite. Not yet integrated with the frontend. |
| `exobios-ai/` | Reserved, not started | Placeholder for the standalone RAG/LLM service the backend's AI gateway already expects to call. See [AI integration](#ai-integration--exobios-ai) below. |

**Frontend and backend are each independently functional but not yet connected.** The
frontend runs entirely on mock data seeded into `localStorage`, by design, so it can be
developed and demoed without a live API. The backend exposes a complete REST API of its
own and can be run and tested in isolation via Postman/Swagger. Wiring the two together
is the next major milestone — see [Known limitations](#known-limitations).

```
                     ┌───────────────────┐        (not yet wired)        ┌──────────────────────┐
   ASHA / Doctor ───▶│  exobios-frontend │╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌▶│   exobios-backend     │
   / Admin            │  Vue 3 PWA        │        REST + JWT             │   Spring Boot API     │
                     └───────────────────┘                               └──────────┬────────────┘
                                                                                      │ POST /analyze
                                                                                      │ X-Api-Key
                                                                                      ▼
                                                                          ┌──────────────────────┐
                                                                          │   exobios-ai          │
                                                                          │   (reserved — not      │
                                                                          │    built yet)          │
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

The backend already speaks a complete contract to an external AI service — it just
doesn't exist yet:

- On `POST /assessments/{id}/submit`, `AssessmentService` synchronously calls
  `AiGateway.analyzeAssessment(...)`, which posts the assessment (complaint, symptoms,
  vitals, history) to `${AI_SERVICE_URL}/analyze` with an `X-Api-Key` header.
- Response (`risk level`, `summary`, `red flags`, `recommendations`, `confidence`) is
  persisted 1:1 against the assessment and mirrored onto `assessments.risk_level` for
  analytics.
- If the AI service is unreachable (2 retries, 5s connect / 30s read timeout), the
  gateway falls back to a `PENDING` placeholder result rather than failing the request.
- `exobios-ai/` is reserved for this service — a RAG-based clinical decision-support API
  (red-flag detection, risk classification, referral-urgency guidance) grounded in
  approved clinical protocols (IMNCI/national CHW guidelines). It is planned, not yet
  implemented; `docker-compose.yml` already wires the env vars (`AI_SERVICE_URL`,
  `AI_API_KEY`) it will need.

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
  recommendations are static placeholder content, not a real model. The backend's AI
  gateway contract is real and wired, but has no live AI service behind it yet — see
  [AI integration](#ai-integration--exobios-ai).
- Frontend reports page is static demo data, not derived from the patient/assessment
  stores.
- AI-assisted results on the backend are computed **synchronously** inside the
  assessment-submit request — there's no async/queue path yet, so a slow or unreachable
  AI service directly extends submit latency (mitigated today by the retry/timeout/
  placeholder-fallback behavior in `AiGateway`).
