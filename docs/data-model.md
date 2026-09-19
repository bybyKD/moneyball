# Moneyball — Data Model

All tables are created by a single Alembic revision
(`apps/api/migrations/versions/7c3be29972d5_initial_full_schema.py`), applied to
dev and test DBs. Foreign-key styles: `snake_case` column names, BigInteger PKs.

## Core football (domain)

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `leagues` | Leagues | `name(str, unique)`, `country`, `provider`, `level` |
| `competitions` | Tournaments within leagues | `league_id`, `name`, `provider` |
| `seasons` | `2020/21`…`2024/25` | `name(str, unique)`, `start_year`, `provider` |
| `clubs` | Clubs | `name`, `league_id`, `slug`, `provider`, `_profiles(JSON)` |
| `players` | Players | `full_name`, `slug`, `dob`, `nationality_code/name`, `height_cm`, `preferred_foot`, `primary_position`, `current_club_id`, `profile(JSON)` |
| `player_positions` | Additional positions | `player_id`, `position` |
| `player_roles` | Role tags | `player_id`, `role` |
| `player_season_stats` | Per player·season·competition | **55 cols** (goals, xG, xA, passes, duels, carries, dribbles, …), `UniqueConstraint(player/season/competition)`, `position` |
| `player_match_stats` | Per match (future optional) | player, match stats |

## Analytics / semantic (spec §24)

| Table | Purpose |
|-------|---------|
| `player_embeddings` | `player_id`, `kind` (`tactical_profile`), `text`, `embedding VECTOR(512)` (HNSW L2 index `ix_pe_vector`), `model` (`moneyball_v1`), `provider` |

## Scouting workspace (spec §19–21)

| Table | Purpose |
|-------|---------|
| `scouting_missions` | user mission: title, `query_text`, `constraints(JSON)`, `weights(JSON)`, status (`draft/running/complete`) |
| `mission_candidates` | ranked results: `rank`, `score`, `evidence(JSON)`, `status` |
| `shortlists` / `shortlist_players` | user shortlists → `status`, `priority`, `notes` |
| `player_comparisons` | saved head-to-head: `player_ids`, `custom_weights`, `result(JSON)` |
| `scouting_reports` | persisted report drafts: `body`, `verification_status`, `confidence`, `format_type`, `source_ids` |

## Agents (spec §17)

| Table | Purpose |
|-------|---------|
| `agent_runs` | mission → run: `request`, `status`, `mission_plan`, `final_output`, `total_duration_ms`, `total_llm_calls`, `total_cost_usd` |
| `agent_tasks` | one row per agent step: `agent`, `note`, `input_data/output_data`, `duration_ms`, `llm_calls`, `cost_usd` |
| `agent_events` | full event trace: `seq`, `kind`, `action`, `tool`, `payload` |

## Market & context (spec §22, §35)

| Table | Purpose |
|-------|---------|
| `sources` | provenance (`provider`, `kind`, `url`, `attribution_required`) |
| `transfers` | fees (`fee_eur`, `reported_fee`, `is_rumored`, `source_id`) |
| `market_values` | value history (`value_eur`, `is_estimate`, `source_id`) |
| `contracts` | `weekly_wages_eur`, `clauses`, `source_id` |
| `injuries` | `injury_type`, `days_missed`, `matches_missed`, `source_id` |

## Auth

| Table | Purpose |
|-------|---------|
| `users` | email (unique), display name, PBKDF2 password hash, status |

## Demo data (deterministic)

`make seed` (`scripts/seed_demo.py`, deterministic `RNG = random.Random(42069)`):
- 18 leagues (EPL, La Liga, …), 220 clubs (exactly, via `divmod`), 5 seasons,
  5,000 players with coherent stats per position distribution, current-season
  `player_season_stats`.
- `make embed` adds pgvector embeddings for the same 5,000 players.

`player_embeddings`, scouting, market and auth tables are intentionally seeded
sparsely — they are *filled by the product* (missions, comparisons, value runs,
reports) rather than pre-seeded.