"""Analytics routes — Moneyball metrics for a single player (spec §20/§26).

GET /api/players/{player_id}/analytics
    per-90 metrics + position-cohort percentiles + composite score + value.

Percentiles are computed live against the position cohort for the same season
the target played in. All deterministic (no LLM); see services.analytics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.errors import NotFoundError
from apps.api.app.db.models.football import Player, PlayerSeasonStat
from apps.api.app.db.session import get_session
from apps.api.app.services.player_analytics import analyze_stat

router = APIRouter(prefix="/players", tags=["analytics"])


@router.get("/{player_id}/analytics")
async def player_analytics(player_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    player = await session.get(Player, player_id)
    if player is None:
        raise NotFoundError("Player not found")

    # current-season stat row for the target
    stats = (
        await session.scalars(
            select(PlayerSeasonStat)
            .where(PlayerSeasonStat.player_id == player_id)
            .order_by(PlayerSeasonStat.minutes_played.desc())
        )
    ).all()
    if not stats:
        raise NotFoundError("No season stats for this player yet (run make seed)")

    target = stats[0]

    # cohort = same position + same season (incl. the target)
    cohort = (
        await session.scalars(
            select(PlayerSeasonStat).where(
                PlayerSeasonStat.position == target.position,
                PlayerSeasonStat.season_id == target.season_id,
            )
        )
    ).all()

    return {
        "player_id": player_id,
        "player_name": player.full_name,
        "result": analyze_stat(target, cohort, player.date_of_birth),
    }