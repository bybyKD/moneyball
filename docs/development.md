# Moneyball — Development

## Quick start

```bash
# 1. Infra (Postgres 54320, Postgres test 54321, Redis 6379)
docker compose up -d                     # or: make infra-up / docker compose down

# 2. Python env
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# 3. Node deps (workspaces incl. web)
npm install

# 4. Config
cp .env.example .env                     # already matches the compose ports

# 5. Database
make migrate                             # alembic upgrade head (dev DB)
DATABASE_URL="postgresql+psycopg://moneyball:moneyball@localhost:54321/moneyball_test" make migrate
                                         # apply the same migration to the test DB

# 6. Demo data
make seed                                # 5,000 players / 220 clubs / 18 leagues
make embed                               # pgvector lookalike vectors

# 7. Run
make api-dev                             # FastAPI on :8000 → http://localhost:8000/docs
# (terminal 2)
npm run dev -w apps/web                  # Next.js on :3000 → http://localhost:3000

# 8. Tests
make api-test                            # pytest, boots :8008 against test DB
```

## Make targets

| Target            | Purpose |
|-------------------|---------|
| `infra-up`        | `docker compose up -d` |
| `migrate`         | Alembic upgrade to head (dev); re-run with test `DATABASE_URL` for 54321 |
| `migrate-downgrade` | Alembic downgrade one rev |
| `seed`            | Load demo roster (idempotent) |
| `embed`           | Build pgvector embeddings (idempotent) |
| `api-dev`         | uvicorn with reload on :8000 |
| `api-test`        | pytest `apps/api/tests` |
| `web-dev`         | `npm run dev -w apps/web` |

## Env vars (`.env`)

```
DATABASE_URL=postgresql+psycopg://moneyball:moneyball@localhost:54320/moneyball
TEST_DATABASE_URL=…:54321/moneyball_test
```
The API also reads `API_ROOT_PATH=/api`, `AUTH_COOKIE_NAME=moneyball_session`,
`AUTH_COOKIE_SECURE=false`, `EMBEDDING_DIM=512` (see `apps/api/app/core/config.py`).

## Python conventions

- **Imports run from repo root**: `python -m apps.api.app.scripts.seed_demo`.
- Services hold all logic; routes stay thin (no business rules in route bodies).
- Every number is deterministic — no RNG (except the demo seed), no LLM calls.
- New tables → edit models (`apps/api/app/db/models/*`), then
  `alembic -c apps/api/alembic.ini revision --autogenerate`.

## Testing

`apps/api/tests/test_smoke.py` boots uvicorn on **:8008** against the **test
DB**, registering users with UUID emails (idempotent). It covers: health, auth,
players, analytics, semantic lookalikes, market value-picks, mission →
shortlist → agent report, and head-to-head compare.

## Web conventions

- Server components fetch `${NEXT_PUBLIC_API_URL}` (default
  `http://localhost:8000`); auth pages forward the session cookie read via
  `cookies()` from `next/headers`.
- Client components call `/api/...` (Next rewrite proxies to :8000).
- Palette: `#0e1626` (bg), `#1f2c44` (borders), `#8cbfff` (accent),
  `#8fa0bd` (muted).

## Where things live

```
apps/api/app/
  api/routes/    auth, users, players, analytics, similar, market, compare,
                 scouting (missions+shortlists), agents
  services/      analytics, player_analytics, scouting, agents, market,
                 comparison, embeddings
  scripts/       seed_demo (make seed), embed_demo (make embed)
  db/models/     football, scouting, agents, market, embeddings, auth
  migrations/    alembic
apps/web/app/    home, players(+detail), scouting, market, analytics,
                 embedding, shortlists, agents, reports, compare, settings
```

## Adding an API route (10-minute loop)

1. Service function in `apps/api/app/services/<domain>.py`.
2. Router in `apps/api/app/api/routes/<domain>.py`; register it in
   `api/router.py`.
3. `curl` against `:8008` (boot with the test `DATABASE_URL`).
4. Add a smoke test; `make api-test`.
5. Commit + push.