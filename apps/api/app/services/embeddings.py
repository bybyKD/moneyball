"""pgvector embeddings (spec §24) — deterministic, reproducible, no models.

Turns structured player stats into a fixed 512-dim semantic vector:
  [ per-90 feature percentiles within the player's position cohort (≈24 dims),
    physical + minutes (≈4 dims),
    position one-hot (8 dims),
    0-padding to 512 ]

All vectors are unit-normalized, so L2 distance (the HNSW index metric) orders
players identically to cosine similarity. model = "moneyball_v1" and
source values are stamped so nothing pretends to be an LLM embedding (spec §38).
"""

from __future__ import annotations

from bisect import bisect_right
from math import sqrt

from apps.api.app.core.config import settings
from apps.api.app.db.models.embeddings import PlayerEmbedding
from apps.api.app.db.models.football import Player, PlayerSeasonStat
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

MODEL_NAME = "moneyball_v1"

RATIO_FEATURES = {
    "pass_completion": ("passes_completed", "passes_attempted"),
    "defensive_duel_win": ("defensive_duels_won", "defensive_duels_total"),
    "aerial_duel_win": ("aerial_duels_won", "aerial_duels_total"),
}
COUNT_FEATURES = [
    "goals_per90", "assists_per90", "xg_per90", "xa_per90", "shots_per90",
    "shots_on_target_per90", "key_passes_per90", "progressive_passes_per90",
    "carries_per90", "progressive_carries_per90", "successful_dribbles_per90",
    "interceptions_per90", "tackles_per90", "ball_recoveries_per90",
    "clearances_per90", "touches_per90", "touches_in_box_per90",
]
COUNT_COL = {
    "goals_per90": "goals", "assists_per90": "assists", "xg_per90": "xg", "xa_per90": "xa",
    "shots_per90": "shots", "shots_on_target_per90": "shots_on_target",
    "key_passes_per90": "key_passes", "progressive_passes_per90": "progressive_passes",
    "carries_per90": "carries", "progressive_carries_per90": "progressive_carries",
    "successful_dribbles_per90": "successful_dribbles", "interceptions_per90": "interceptions",
    "tackles_per90": "tackles", "ball_recoveries_per90": "ball_recoveries",
    "clearances_per90": "clearances", "touches_per90": "touches", "touches_in_box_per90": "touches_in_box",
}
POSITIONS = ["GK", "CB", "FB", "DM", "CM", "AM", "W", "ST"]


def per90(raw, minutes: int) -> float:
    if minutes is None or minutes < 90:
        return 0.0
    return raw * 900.0 / minutes if isinstance(raw, (int, float)) else 0.0


def _feature(row, name: str) -> float:
    if name in RATIO_FEATURES:
        won_c, total_c = RATIO_FEATURES[name]
        total = getattr(row, total_c, None) or 0
        won = getattr(row, won_c, None) or 0
        return won / total if total else 0.0
    if name == "xgi_per90":
        return per90((row.xg or 0) + (row.assists or 0) * 0.72, row.minutes_played or 0)
    return per90(getattr(row, COUNT_COL[name], None) or 0, row.minutes_played or 0)


def _normalize(v: list[float]) -> list[float]:
    norm = sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def _vector(features: list[float]) -> list[float]:
    vec = features + [0.0] * (settings.embedding_dim - len(features))
    return _normalize(vec)


def _feature_text(row, position: str) -> str:
    brief = [
        f"{name}={_feature(row, name):.3f}"
        for name in COUNT_FEATURES + list(RATIO_FEATURES)
    ]
    return f"position={position} " + " ".join(brief)


async def build_all_embeddings(session: AsyncSession, provider: str | None = None, batch_size: int = 500) -> dict:
    """Recompute embeddings for every player of a data provider (one row/player).

    Cohorts are scoped to the provider so statsbomb and demo vectors never mix;
    rows are stamped with the provider and model so re-seeding a different
    dataset leaves previous providers untouched.
    """
    provider = provider or settings.default_provider
    rows = (
        await session.scalars(
            select(PlayerSeasonStat)
            .where(PlayerSeasonStat.provider == provider)
            .order_by(PlayerSeasonStat.player_id, PlayerSeasonStat.minutes_played.desc())
        )
    ).all()
    by_player: dict[int, PlayerSeasonStat] = {}
    for r in rows:
        by_player.setdefault(r.player_id, r)
    stats = list(by_player.values())

    # per-feature percentile arrays within position cohort
    percentile_sorted: dict[str, dict[str, list[float]]] = {}
    for pos in POSITIONS:
        cohort = [r for r in stats if r.position == pos]
        pos_sorted = {}
        for f in COUNT_FEATURES:
            vals = sorted(x for x in (_feature(r, f) for r in cohort) if x > 0)
            pos_sorted[f] = vals
        percentile_sorted[pos] = pos_sorted

    def pct(pos, f, value) -> float:
        vals = percentile_sorted.get(pos, {}).get(f, [])
        if not vals:
            return 0.0
        if value <= 0:
            return 0.0
        return bisect_right(vals, value) / len(vals)

    player_ids = sorted(by_player)
    players = {
        p.id: p
        for p in (
            await session.scalars(select(Player).where(Player.id.in_(player_ids)))
        ).all()
    }

    await session.execute(
        delete(PlayerEmbedding).where(
            PlayerEmbedding.model == MODEL_NAME,
            PlayerEmbedding.provider == provider,
        )
    )

    count = 0
    embeds = []
    for pid in player_ids:
        row = by_player[pid]
        pos = row.position
        feats = [pct(pos, f, _feature(row, f)) for f in COUNT_FEATURES]
        for ratio in RATIO_FEATURES:
            feats.append(_feature(row, ratio))
        feats.append(min(1.0, (row.minutes_played or 0) / 3000.0))
        player = players.get(pid)
        feats.append(min(1.0, (player.height_cm or 160) / 210.0) if player else 0.0)
        feats.append(0.0 if player is None or player.date_of_birth is None else min(1.0, (2025 - player.date_of_birth.year) / 45.0))
        feats += [1.0 if POSITIONS.index(pos) == i else 0.0 for i in range(len(POSITIONS))]

        name = player.full_name if player else f"player_{pid}"
        embeds.append(
            PlayerEmbedding(
                player_id=pid,
                kind="tactical_profile",
                text=name,  # short text description
                embedding=_vector(feats),
                model=MODEL_NAME,
                provider=provider,
            )
        )
        count += 1
        if len(embeds) >= batch_size:
            session.add_all(embeds)
            await session.commit()
            embeds = []
    if embeds:
        session.add_all(embeds)
        await session.commit()
    return {"embedded": count, "model": MODEL_NAME, "provider": provider, "dims": settings.embedding_dim}
