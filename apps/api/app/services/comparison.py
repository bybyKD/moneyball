"""Comparison service (spec §20) — head-to-head Moneyball breakdown.

Runs the analytics engine for two (or more) players and aligns their
metric sets into a side-by-side comparison: per-90 output, position-cohort
percentiles, composite score, market value.
"""

from __future__ import annotations

from apps.api.app.core.config import settings
from apps.api.app.db.models.football import Player, PlayerSeasonStat
from apps.api.app.services.player_analytics import analyze_stat
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _one(session: AsyncSession, player_id: int, provider: str | None = None) -> dict:
    provider = provider or settings.default_provider
    player = await session.get(Player, player_id)
    if player is None:
        return {"player_id": player_id, "error": "not_found"}
    stat = await session.scalar(
        select(PlayerSeasonStat)
        .where(
            PlayerSeasonStat.player_id == player_id,
            PlayerSeasonStat.provider == provider,
        )
        .order_by(PlayerSeasonStat.minutes_played.desc())
    )
    if stat is None:
        return {
            "player_id": player_id,
            "name": player.full_name,
            "position": player.primary_position,
            "score": None,
            "market_value_eur": None,
            "minutes": None,
            "per90": {},
            "percentiles": {},
        }
    cohort = (
        await session.scalars(
            select(PlayerSeasonStat).where(
                PlayerSeasonStat.position == stat.position,
                PlayerSeasonStat.season_id == stat.season_id,
                PlayerSeasonStat.provider == provider,
            )
        )
    ).all()
    result = analyze_stat(stat, cohort, player.date_of_birth)
    return {
        "player_id": player_id,
        "name": player.full_name,
        "position": result["position"],
        "score": result["score"],
        "market_value_eur": result["market_value_eur"],
        "minutes": result["minutes_played"],
        "per90": result["per90"],
        "percentiles": result["percentiles"],
    }


async def compare_players(session: AsyncSession, player_ids: list[int], provider: str | None = None) -> dict:
    sides = [await _one(session, pid, provider=provider) for pid in player_ids]
    valid = [s for s in sides if not s.get("error")]
    if not valid:
        return {"players": sides, "verdict": "no comparable players"}
    metric_keys: list[str] = []
    for s in valid:
        for k in s["percentiles"]:
            if k not in metric_keys:
                metric_keys.append(k)
    metric_keys.sort()

    winner = None
    if len(valid) >= 2 and all(s["score"] is not None for s in valid):
        winner = max(valid, key=lambda s: s["score"])

    return {
        "players": sides,
        "metrics": metric_keys,
        "winner": {"player_id": winner["player_id"], "name": winner["name"], "score": winner["score"]} if winner else None,
    }
