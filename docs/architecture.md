# Moneyball Platform — Architecture

An AI-assisted football scouting platform. The guiding rule (spec §38): **every
number is deterministic and reproducible** — analytics, scoring, market values,
embeddings and agent outputs are computed from structured SQL statistics with no
LLM requirement. AI providers are pluggable; the app ships in a zero-LLM
fallback mode by default.

## Stack

| Layer    | Tech |
|----------|------|
| API      | FastAPI + SQLAlchemy 2 (async) + Pydantic v2 |
| DB       | PostgreSQL 16 + pgvector (HNSW), Redis |
| Migrations | Alembic (`apps/api/migrations`) |
| Web      | Next.js 15 (App Router) + React 19 + Tailwind 3 |
| Infra    | Docker Compose (`postgres` 54320, `postgres_test` 54321, redis 6379) |
| Tests    | pytest + httpx against a live uvicorn on `:8008` / test DB |

Repo is an npm workspace monorepo (`apps/api`, `apps/web`, `packages/`),
flattened at the Python level via the `apps.api.app.*` import convention
(imports are executed from the repo root).

## Request flow

```
Browser(web :3000)
   │  /api/*  (rewrite proxy → 8000)
   ▼
Next server component / client component
   │  fetch(API)  [cookie forwarded for auth pages]
   ▼
FastAPI router (apps/api/app/api/routes/*)
   │  Depends(get_session) async session
   ▼
Service layer (apps/api/app/services/*) — all decisions here
   │
   ├─ analytics.py        per-90, percentiles, composite score, value
   ├─ player_analytics.py single-player report vs position cohort
   ├─ scouting.py         mission engine: score every player in a position
   ├─ agents.py           reference pipeline: plan→collect→analyze→review→write
   ├─ market.py           value picks + position summary
   ├─ comparison.py       head-to-head alignments
   └─ embeddings.py       512-dim pgvector build (moneyball_demo_v1)
   ▼
SQLAlchemy models (apps/api/app/db/models/*) → Postgres
```

## Data pipeline

```text
make seed   → demo roster (5,000 players, 18 leagues, 220 clubs, 5 seasons)
make embed  → deterministic pgvector embeddings for semantic lookalikes
```

Both are idempotent (seed resets demo rows; embed deletes its model's rows and
rebuilds).

## Deterministic analytics (§20)

- **per-90**: `value * 900 / minutes`, only when `minutes >= 90`.
- **Percentile**: `bisect_right(sorted_cohort, value) / len(cohort)` within the
  player's position for the same season. Some weights are lower-is-better
  (normalized as `1 - percentile`).
- **Moneyball score** (0–100): position-weighted sum of normalized percentiles
  (`POSITION_WEIGHTS` in `services/analytics.py`).
- **Market value** (`estimate_market_value`): EUR estimate from score^3 ×
  position pay factor × age factor. `value_picks` ranks `score / ln(value+1)` —
  production-per-euro.

## Semantic search (§24)

`services/embeddings.py` builds one 512-dim vector per player:
`[position-cohort percentiles (17) · ratios+physical+minutes (~6) · position
one-hot (8) | 0-padding to 512]`, unit-normalized so L2 distance on the HNSW
index ordering ≡ cosine similarity. Stamped `model = moneyball_demo_v1`, kept
visibly distinct from any future LLM embedding.

## Agents (§10–§17, §38)

`run_agent_pipeline` runs a deterministic squad as `AgentRun/AgentTask/AgentEvent`
rows: orchestrator (plan) → data_collector → analyst → reviewer (doctrine checks
e.g. `insufficient_sample`) → writer (report). `total_llm_calls = 0`,
`total_cost_usd = 0` in fallback mode — the trace is honest about what computed
what. A future provider adapter only swaps the "analyst"/"writer" steps while the
evidence chain stays intact.

## Testing

`make api-test` → pytest boots uvicorn (`:8008`, test DB 54321) and exercises the
full product loop; emails are UUID-scoped so runs are idempotent.