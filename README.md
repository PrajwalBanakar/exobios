# Exobios — AI-Assisted Healthcare Platform

Exobios is a field-health platform built for India's community health worker network
(ASHA, ANM, CHO, LHV, Health Assistants) and MBBS Doctors. A health worker registers a
patient, walks through a structured symptom/history/examination intake, and gets an
AI-assisted differential diagnosis and a role-aware plan of action (referral, ambulance,
or teleconsultation).

This repository is a monorepo with three parts:

| Folder | Status | Description |
|---|---|---|
| `exobios-frontend/` | **Active — this release** | Vue 3 PWA. Fully functional against mock/local data; not yet wired to a live backend. |
| `exobios-backend/` | In progress | Spring Boot API (Java 21). Domain modules exist (auth, patients, users, clinical, analytics, field-ops, audit) but is not yet integrated with the frontend. |
| `exobios-ai/` | Not started | Reserved for the AI diagnosis service. |

**This release covers the frontend only.** The backend is a separate, independently
evolving service — the frontend currently runs entirely on mock data seeded into
`localStorage`, by design, so it can be developed and demoed without a live API.

---

## Frontend — Tech Stack

- **Vue 3** (Composition API, `<script setup>`)
- **Vite** — dev server & build
- **Pinia** — state management
- **Vue Router 4**
- **Tailwind CSS**
- **vite-plugin-pwa** — installable PWA (manifest, service worker, offline app shell)
- **Vitest** + **@vue/test-utils** + **@testing-library/vue** — unit tests
- Custom i18n (English / Hindi / Kannada)

## Frontend — Architecture

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
  offline/     offline queue + network-status detection
```

Role model: every logged-in user resolves to one `roleCategory` — `PARAMEDIC`
(ASHA/ANM/CHO/LHV/Health Assistant), `DOCTOR` (MBBS Doctor), or `ADMIN` (Super Admin) —
which drives which examination module, plan-of-action options, and teleconsult doctor
tier a user sees.

## Setup

Requires Node.js 18+.

```bash
cd exobios-frontend
npm install
```

## Run (development)

```bash
npm run dev
```

Starts the Vite dev server (defaults to `http://localhost:5173`, or the next free port).
Sign up as any role (ASHA/ANM/CHO/LHV/Health Assistant/MBBS Doctor) from the login
screen — accounts are stored in `localStorage`, no backend required.

## Build (production)

```bash
npm run build      # outputs to exobios-frontend/dist/
npm run preview    # serve the production build locally
```

## Test

```bash
npm run test         # run once
npm run test:watch   # watch mode
npm run test:ui      # Vitest UI
```

## Known Limitations (mock-data phase)

- No live backend integration — patients, referrals, and teleconsult sessions are
  seeded/mutated entirely in `localStorage`/memory.
- `referrals` and `teleconsult` Pinia stores are in-memory only (they reset on a full
  page reload); `patients` and `auth` do persist to `localStorage`.
- AI differential diagnosis, treatment protocols, and investigation recommendations are
  static placeholder content, not a real model.
- Reports page is static demo data, not derived from the patient/assessment stores.
