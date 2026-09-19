"""Scouting service (spec §10—§17) — run missions against the demo roster.

Deterministic: for a mission's position, every player's Moneyball score is
computed from their current-season stats ranked within the position cohort
(reuses services.analytics + player_analytics). O(n·k) with n = players,
k = weight metrics, using pre-sorted cohort arrays for percentile lookups
instead of scanning the cohort per player.
"""

from __future__ import annotations

from bisect import bisect_right

from apps.api.app.core.config import settings
from apps.api.app.db.models.football import Player, PlayerSeasonStat
from apps.api.app.db.models.scouting import MissionCandidate
from apps.api.app.services.analytics import POSITION_WEIGHTS, per90
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _pps(row, col: str) -> float | None:
    """Per-90 of a raw count column (None for thin sample)."""
    minutes = row.minutes_played or 0
    raw = getattr(row, col, None)
    return per90(raw, minutes)


FEATURE_COL = {
    "interceptions_per90": "interceptions",
    "clearances_per90": "clearances",
    "carries_per90": "carries",
    "progressive_carries_per90": "progressive_carries",
    "ball_recoveries_per90": "ball_recoveries",
    "key_passes_per90": "key_passes",
    "progressive_passes_per90": "progressive_passes",
    "xa_per90": "xa",
    "xg_per90": "xg",
    "goals_per90": "goals",
    "assists_per90": "assists",
    "successful_dribbles_per90": "successful_dribbles",
    "shot_creating_actions_per90": "shot_creating_actions",
    "touches_per90": "touches",
    "touches_in_box_per90": "touches_in_box",
}

RATIO_FEATURES = {
    "tackles_win_rate": ("defensive_duels_won", "defensive_duels_total"),
    "aerial_win_rate": ("aerial_duels_won", "aerial_duels_total"),
    "pass_completion": ("passes_completed", "passes_attempted"),
}


def _feature_value(row, weight_key: str) -> float | None:
    if weight_key in FEATURE_COL:
        return _pps(row, FEATURE_COL[weight_key])
    if weight_key == "xgi_per90":
        xg = float(getattr(row, "xg", 0) or 0)
        assists = int(getattr(row, "assists", 0) or 0)
        return per90(xg + assists * 0.72, row.minutes_played or 0)
    won_c, tot_c = RATIO_FEATURES.get(weight_key, (None, None))
    if won_c is None:
        return None
    total = getattr(row, tot_c, None) or 0
    won = getattr(row, won_c, None) or 0
    return won / total if total else None


async def score_players_for_position(
    session: AsyncSession, position: str, provider: str | None = None
):
    """Score all players in a position; return [{player, stat, score, metrics}].

    Cohort = one row per player (most-minutes current-ish season row) and is
    scoped to a single data provider so statsbomb and demo rows never mix.
    Lower-is-better weights are normalized by (1 - percentile).
    """
    provider = provider or settings.default_provider
    weights = POSITION_WEIGHTS.get(position)
    if not weights:
        return []

    rows = (
        await session.scalars(
            select(PlayerSeasonStat)
            .where(
                PlayerSeasonStat.position == position,
                PlayerSeasonStat.provider == provider,
            )
            .order_by(PlayerSeasonStat.player_id, PlayerSeasonStat.minutes_played.desc())
        )
    ).all()

    # one row per player (top minutes), keep raw + feature values
    by_player: dict[int, PlayerSeasonStat] = {}
    for r in rows:
        if r.player_id not in by_player:
            by_player[r.player_id] = r
    stats = list(by_player.values())

    # precompute feature value arrays per weight key for percentile lookup
    feature_values: dict[str, list[float]] = {}
    for wk in weights:
        base = wk.removesuffix("_pctile")
        vals = [_feature_value(r, base) for r in stats]
        vals = [v for v in vals if v is not None]
        feature_values[wk] = sorted(vals)

    player_ids = [r.player_id for r in stats]
    players = {
        p.id: p
        for p in (
            await session.scalars(
                select(Player).where(Player.id.in_(player_ids))
            )
        ).all()
    }

    scored = []
    for r in stats:
        weighted = 0.0
        used_w = 0.0
        metrics = {}
        for wk, (w, higher_better) in weights.items():
            base = wk.removesuffix("_pctile")
            v = _feature_value(r, base)
            if v is None:
                continue
            cohort = feature_values[wk]
            pct = bisect_right(cohort, v) / len(cohort)
            norm = pct if higher_better else 1.0 - pct
            weighted += w * norm
            used_w += w
            metrics[base] = round(v, 3)
        if used_w <= 0:
            continue
        score = round(100.0 * weighted / used_w, 1)
        scored.append(
            {
                "player": players.get(r.player_id),
                "stat": r,
                "score": score,
                "metrics": metrics,
            }
        )

    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored


async def run_mission(session: AsyncSession, mission, position: str, top_n: int = 50, provider: str | None = None):
    """Rank candidates for a finished mission and store MissionCandidate rows."""
    scored = await score_players_for_position(session, position, provider=provider)
    existing = {
        c.player_id: c
        for c in (
            await session.scalars(
                select(MissionCandidate).where(MissionCandidate.mission_id == mission.id)
            )
        ).all()
    }

    for rank, s in enumerate(scored[:top_n], start=1):
        player = s["player"]
        if player is None:
            continue
        cand = existing.get(player.id)
        if cand is None:
            session.add(
                MissionCandidate(
                    mission_id=mission.id,
                    player_id=player.id,
                    rank=rank,
                    score=s["score"],
                    status="candidate",
                    evidence={
                        "position": position,
                        "metrics": s["metrics"],
                        "minutes": s["stat"].minutes_played or 0,
                    },
                )
            )
        else:
            cand.rank = rank
            cand.score = s["score"]
            cand.status = "candidate"
    await session.commit()
    return len(scored)
