# Exobios — AI-Assisted ASHA Worker Healthcare Platform

Monorepo containing all services for the Exobios platform.

## Structure

```
Exobios/
├── exobios-frontend/   Vue 3 + Vite + Tailwind — ASHA Worker web app
├── exobios-backend/    Java 21 + Spring Boot 3 — REST API
├── exobios-ai/         Python FastAPI + LLM — AI analysis service (upcoming)
└── docs/               Architecture, API, database, and deployment docs
```

## Quick Start

### Frontend
```bash
cd exobios-frontend
npm install
npm run dev
```

### Backend
```bash
cd exobios-backend
cp .env.example .env   # fill in values
docker compose up postgres -d
mvn spring-boot:run
```

## Tech Stack

| Layer    | Technology                                    |
|----------|-----------------------------------------------|
| Frontend | Vue 3, Pinia, Tailwind CSS, Vite              |
| Backend  | Java 21, Spring Boot 3, PostgreSQL, Flyway    |
| AI       | Python 3.12, FastAPI, LangChain (upcoming)    |
| Infra    | Docker, Docker Compose                        |
