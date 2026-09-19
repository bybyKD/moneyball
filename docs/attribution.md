# Data sources & attribution

Moneyball's analytics run against real football data wherever possible. Every
row in the database is tagged with a **provider** + **provider_id** so the
origin of a number is always traceable (see `docs/data-model.md`).

## StatsBomb open data (default provider: `statsbomb`)

- **Source:** [statsbomb/open-data](https://github.com/statsbomb/open-data)
  repository, cloned to `data/raw/statsbomb/` (shallow copy, gitignored).
- **License:** StatsBomb free/open data is released under the
  [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](https://github.com/statsbomb/open-data/blob/main/LICENSE.pdf)
  license (CC BY-NC-SA 4.0). Commercial redistribution is not permitted; this
  project is a research/demo platform.
- **Attribution:** We acknowledge StatsBomb (statsbomb.com) as the copyright
  owner of the underlying event and lineup data.

### What is loaded

The loader (`apps/api/app/services/statsbomb.py`) ingests every competition /
season present in `competitions.json`:

- **competitions** → `competitions` + `leagues` (code `SB{competition_id}`)
- **seasons** → `seasons` (keyed `provider_id = {competition_id}/{season_id}`)
- **lineups** → `players`, `clubs`, `player_positions`
- **events** → `player_season_stats` (aggregates computed from StatsBomb event
  types: carries, passes, shots, ball recovery, pressure, duels, etc.)

### Aggregation notes

- Coordinates are StatsBomb pitch space (0–120 x, 0–80 y); attacking direction
  is always +x, so metrics are comparable across teams/matches.
- "Box" = x∈[102,120], y∈[18,62]; "final third" = x ≥ 80.
- Progressive pass/carry: forward advance of ≥10m, or ≥5m with progress
  ≥30% of total distance. Long pass: length ≥ 30m.
- Pressure success: ball recovery / interception / duel won within 6s of a
  press event.
- xA estimated from `assisted_shot_id` → receiver's shot xG. SCA/GCA are
  approximated from passes leading to shots/goals (documented approximation).
- StatsBomb does not publish dates of birth, heights, or preferred foot, so
  those stay `NULL` for `statsbomb` players (no fabrication). Nationality is
  captured from the lineup `country` field when present; `bios_known` is
  nonetheless `false`, because biographical completeness is not guaranteed.

## Demo data (provider: `demo`)

The deterministic demo generator (`apps/api/app/scripts/seed_demo.py`) creates
synthetic clubs/players/statistics for offline QA. It is explicitly labeled
`demo`, isolated per topic, and never mixed into `statsbomb` cohorts.

## Provider isolation guarantee

Analytics, embeddings, market rankings, and comparisons **filter by provider**
throughout (default `statsbomb`). Demo rows can coexist in the same database
without polluting real-data results. Re-seeding one provider leaves the other
untouched.