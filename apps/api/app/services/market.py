"""Market service (spec §22) — Moneyball value ranking.

Finds undervalued players: performance relative to estimated market value.
score is the 0–100 Moneyball composite within the player's position cohort;
value_eur comes from services.analytics.estimate_market_value (age/position
adjusted). value_ratio = score / ln(value_eur + 1) so cheap high-performers
float to the top — the classic Moneyball inefficiency scan.
"""

from __future__ import annotations

import math

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.services.analytics import POSITION_WEIGHTS, estimate_market_value
from apps.api.app.services.scouting import score_players_for_position

POSITIONS = list(POSITION_WEIGHTS.keys())


def _age(player) -> int | None:
    dob = player.date_of_birth
    if dob is None:
        return None
    return (2025 - dob.year) - ((1, 1) < (dob.month, dob.day))


async def value_ranking(session: AsyncSession, position: str | None = None, min_minutes: int = 600, k: int = 10) -> list[dict]:
    positions = [position] if position else list(POSITIONS)
    rows = []
    for pos in positions:
        scored = await score_players_for_position(session, pos)
        for s in scored:
            player = s["player"]
            if player is None:
                continue
            minutes = s["stat"].minutes_played or 0
            if minutes < min_minutes:
                continue
            age = _age(player)
            value = estimate_market_value(s["score"], pos, age)
            rows.append(
                {
                    "player_id": player.id,
                    "name": player.full_name,
                    "position": pos,
                    "nationality": player.nationality_name,
                    "age": age,
                    "height_cm": player.height_cm,
                    "foot": player.preferred_foot,
                    "club_id": player.current_club_id,
                    "minutes": minutes,
                    "score": s["score"],
                    "market_value_eur": value,
                    "value_ratio": round(s["score"] / math.log(value + 1), 2),
                }
            )
    rows.sort(key=lambda r: r["value_ratio"], reverse=True)
    return rows[:k]