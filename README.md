# Moneyball AI Scouting Platform

AI-native football recruitment & scouting intelligence system.

> Identify players whose measurable performance, potential, and tactical
> suitability is greater than what their current market value suggests.

## Stack

| Layer    | Tech                                                            |
| -------- | --------------------------------------------------------------- |
| Web      | Next.js 15 (App Router) · TypeScript (strict) · Tailwind CSS    |
| API      | Python 3.14 · FastAPI · SQLAlchemy 2 (async) · Alembic          |
| DB       | PostgreSQL 16 + pgvector                                        |
| Cache/Q  | Redis 7 (Celery broker in later phases)                         |
| Tests    | pytest (API/analytics) · vitest (shared logic) · Playwright e2e |

## Monorepo layout

```text
apps/web       Next.js frontend (professional football analytics terminal)
apps/api       FastAPI backend (data, analytics, agents, orchestration)
packages/types Shared TypeScript types & API contracts
packages/ui    Shared UI primitives
packages/config Shared build/config (tsconfig, tailwind, eslint)
data/          Seed data generator + Alembic migrations
docs/          Architecture, data model, agents, analytics, data sources
docker/        Docker assets
tools/         Local dev tooling
```

## Quick start

Prerequisites: Docker, Node 20+ (Node 26 used), Python 3.14.

```bash
make infra-up     # start Postgres (pgvector) + Redis
make setup        # install API + web dependencies
make migrate      # run Alembic migrations
make api-dev      # http://localhost:8000
make web-dev      # http://localhost:3000
make seed         # load DEMO DATA (Phase 2)
make test         # run API tests
```

## Configuration

Copy `.env.example` to `.env` and adjust. Secrets are never committed.

## Data integrity promise

- Every number carries a `sample`, `season`, `source`, and `confidence`.
- Analytics are deterministic (SQL/Python), never LLM-invented.
- All seed data is explicitly labeled `DEMO DATA` until a licensed
  provider is wired behind the provider interfaces.