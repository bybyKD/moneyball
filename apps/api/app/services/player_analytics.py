"""Cohort matching (spec §20.3) — per-90 metrics, position-cohort percentiles,
composite Moneyball score, and market value estimation for a PlayerSeasonStat
row. Pure over SQLAlchemy rows; all numbers reproducible (no LLM, no RNG).
"""

from __future__ import annotations

from datetime import date

from apps.api.app.services.analytics import (
    POSITION_WEIGHTS,
    MetricValue,
    composite_score,
    estimate_market_value,
    per90,
    percentile,
)

# metric name -> (raw column, is_ratio_fn)
RAW_FEATURES = {
    "goals_per90": ("goals", None),
    "rg": ("placeholders", None),
}
POSITION_FEATURES = {
    "GK": {
        "save_percent": None,
        "clean_sheet_per90": None,
        "goals_against_per90": None,
        "touches_pctile": "touches_in_box",  # nearest proxy
        "pass_completion_pctile": "passes_per90_proxy",
    },
    "CB": {
        "tackles_win_rate_pctile": "defensive_duels_pctile",
        "aerial_win_rate_pctile": "aerial_duels_pctile",
        "interceptions_per90_pctile": "interceptions",
        "clearances_per90_pctile": "clearances",
        "pass_completion_pctile": "passes_pctile",
    },
    "FB": {
        "tackles_win_rate_pctile": "defensive_duels_pctile",
        "interceptions_per90_pctile": "interceptions",
        "aerial_win_rate_pctile": "aerial_duels_pctile",
        "carries_per90_pctile": "carries",
        "progressive_carries_per90_pctile": "progressive_carries",
    },
    "DM": {
        "tackles_win_rate_pctile": "defensive_duels_pctile",
        "interceptions_per90_pctile": "interceptions",
        "ball_recoveries_per90_pctile": "ball_recoveries",
        "pass_completion_pctile": "passes_pctile",
        "progressive_passes_per90_pctile": "progressive_passes",
    },
    "CM": {
        "pass_completion_pctile": "passes_pctile",
        "progressive_passes_per90_pctile": "progressive_passes",
        "key_passes_per90_pctile": "key_passes",
        "carries_per90_pctile": "carries",
        "progressive_carries_per90_pctile": "progressive_carries",
    },
    "AM": {
        "key_passes_per90_pctile": "key_passes",
        "xa_per90_pctile": "xa",
        "xg_per90_pctile": "xg",
        "goals_per90_pctile": "goals",
        "shot_creating_actions_per90_pctile": "shot_creating_actions",
    },
    "W": {
        "goals_per90_pctile": "goals",
        "xg_per90_pctile": "xg",
        "xa_per90_pctile": "xa",
        "assists_per90_pctile": "assists",
        "successful_dribbles_per90_pctile": "successful_dribbles",
    },
    "ST": {
        "goals_per90_pctile": "goals",
        "xg_per90_pctile": "xg",
        "touches_in_box_per90_pctile": "touches_in_box",
        "xgi_per90_pctile": "xgi",
    },
}


def _max(x) -> float:
    return x if x is not None else 0.0


def _ratio_dummy(row) -> float | None:
    return None


def analyze_stat(row, cohort_rows: list, player_birth_date: date | None) -> dict:
    """Compute full analytics for one PlayerSeasonStat vs its position cohort."""
    position = row.position
    minutes = _max(row.minutes_played)
    features = {}
    for key, col in POSITION_FEATURES.get(position, {}).items():
        if col is None:
            features[f"{key}_raw"] = None
            continue
        raw = _max(getattr(row, col, None))
        if key == "pass_completion_pctile":
            attempted = _max(row.passes_attempted)
            completed = _max(row.passes_completed)
            pct = (completed / attempted) if attempted else None
            cohort = [
                (c.passes_completed / c.passes_attempted)
                if (c.passes_attempted or 0) > 0 else None
                for c in cohort_rows
            ]
            features[key] = percentile(pct, [x for x in cohort if x is not None])
        elif key in ("tackles_win_rate_pctile", "aerial_win_rate_pctile", "defensive_duels_pctile", "aerial_duels_pctile"):
            won_col = "defensive_duels_won" if "defensive" in key or "tackles" in key else "aerial_duels_won"
            total_col = "defensive_duels_total" if "defensive" in key or "tackles" in key else "aerial_duels_total"
            won = _max(getattr(row, won_col, None))
            total = _max(getattr(row, total_col, None))
            ratio = (won / total) if total else None
            cohort = [((c.defensive_duels_won or 0) / (c.defensive_duels_total or 0)) if (c.defensive_duels_total or 0) else None for c in cohort_rows] \
                if "defensive" in key or "tackles" in key else \
                [((c.aerial_duels_won or 0) / (c.aerial_duels_total or 0)) if (c.aerial_duels_total or 0) else None for c in cohort_rows]
            features[key] = percentile(ratio, [x for x in cohort if x is not None])
        elif key in ("save_percent", "clean_sheet_per90", "goals_against_per90", "passes_pctile", "passes_per90_proxy"):
            features[key] = None
        elif key == "xgi_per90_pctile":
            raw_val = _max(row.xg) + _max(row.assists) * 0.72
            cohort = [_max(c.xg) + _max(c.assists) * 0.72 for c in cohort_rows]
            features[key] = percentile(per90(raw_val, minutes), [per90(v, c.minutes_played) for v, c in zip(cohort, cohort_rows)])
        else:
            raw_val = _max(getattr(row, col, None))
            value = per90(raw_val, minutes)
            cohort = [per90(_max(getattr(c, col, None)), _max(c.minutes_played)) for c in cohort_rows]
            features[key] = percentile(value, [v for v in cohort if v is not None])

    metrics = [MetricValue(name=k, value=features.get(k), percentile=features.get(k)) for k in POSITION_WEIGHTS.get(position, {})]

    # compute raw per-90 display too
    raw_per90 = {}
    for col in ("goals", "assists", "xg", "xa", "shots", "key_passes"):
        raw_per90[col] = per90(_max(getattr(row, col, None)), minutes)

    score = composite_score(metrics, position)
    age = None
    if player_birth_date is not None:
        today = date(2025, 1, 1)
        age = (today.year - player_birth_date.year) - ((today.month, today.day) < (player_birth_date.month, player_birth_date.day))
    value_eur = estimate_market_value(score, position, age)

    return {
        "position": position,
        "score": score,
        "market_value_eur": value_eur,
        "minutes_played": minutes,
        "per90": raw_per90,
        "percentiles": features,
    }
