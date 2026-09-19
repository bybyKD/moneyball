"""Deterministic analytics engine (spec §20 Metric Science, §22 Scoring).

Pure functions — no LLM, no randomness — over PlayerSeasonStat rows:

* per-90: rates are converted from raw counts using minutes_played
* percentile: a metric's rank within its position cohort (0..1)
* composite Moneyball-style score (0..100): position-weighted, on percentiles
* market value estimate (EUR): composite score, position pay multiplier, age

The rule weights below are static domain heuristics hard-coded per position
(spec §20.3 lays out "ruleset + weights first"). Everything is reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isinf, isnan

POSITION_PAY = {
    "GK": 1.0, "CB": 1.0, "FB": 0.9, "DM": 1.0, "CM": 1.1,
    "AM": 1.15, "W": 1.25, "ST": 1.3,
}

# name -> (weight_within_position, higher_is_better)
POSITION_WEIGHTS: dict[str, dict[str, tuple[float, bool]]] = {
    "GK": {
        "save_percent_pctile": (0.30, True),
        "clean_sheet_per90_pctile": (0.25, True),
        "goals_against_per90_pctile": (0.20, False),
        "touches_pctile": (0.10, True),
        "pass_completion_pctile": (0.15, True),
    },
    "CB": {
        "tackles_win_rate_pctile": (0.20, True),
        "aerial_win_rate_pctile": (0.20, True),
        "interceptions_per90_pctile": (0.15, True),
        "clearances_per90_pctile": (0.10, True),
        "pass_completion_pctile": (0.15, True),
        "aerial_duels_total_pctile": (0.10, True),
        "touches_pctile": (0.10, True),
    },
    "FB": {
        "tackles_win_rate_pctile": (0.20, True),
        "interceptions_per90_pctile": (0.15, True),
        "aerial_win_rate_pctile": (0.10, True),
        "carries_per90_pctile": (0.15, True),
        "progressive_carries_per90_pctile": (0.15, True),
        "pass_completion_pctile": (0.15, True),
        "key_passes_per90_pctile": (0.10, True),
    },
    "DM": {
        "tackles_win_rate_pctile": (0.20, True),
        "interceptions_per90_pctile": (0.15, True),
        "ball_recoveries_per90_pctile": (0.15, True),
        "pass_completion_pctile": (0.20, True),
        "progressive_passes_per90_pctile": (0.15, True),
        "touches_pctile": (0.15, True),
    },
    "CM": {
        "pass_completion_pctile": (0.20, True),
        "progressive_passes_per90_pctile": (0.20, True),
        "key_passes_per90_pctile": (0.15, True),
        "touches_pctile": (0.15, True),
        "progressive_carries_per90_pctile": (0.10, True),
        "interceptions_per90_pctile": (0.10, True),
        "tackles_win_rate_pctile": (0.10, True),
    },
    "AM": {
        "key_passes_per90_pctile": (0.25, True),
        "xa_per90_pctile": (0.25, True),
        "xg_per90_pctile": (0.10, True),
        "goals_per90_pctile": (0.10, True),
        "shot_creating_actions_per90_pctile": (0.20, True),
        "carries_per90_pctile": (0.10, True),
    },
    "W": {
        "goals_per90_pctile": (0.20, True),
        "xg_per90_pctile": (0.20, True),
        "xa_per90_pctile": (0.15, True),
        "assists_per90_pctile": (0.15, True),
        "successful_dribbles_per90_pctile": (0.15, True),
        "key_passes_per90_pctile": (0.15, True),
    },
    "ST": {
        "goals_per90_pctile": (0.35, True),
        "xg_per90_pctile": (0.30, True),
        "touches_in_box_per90_pctile": (0.15, True),
        "xgi_per90_pctile": (0.20, True),
    },
}


@dataclass(frozen=True)
class MetricValue:
    name: str
    value: float | None
    percentile: float | None  # 0..1 within position cohort


def _safe(x: float | None) -> bool:
    return x is not None and not isnan(x) and not isinf(x)


def per90(raw: float | None, minutes: float | None) -> float | None:
    """Rate a raw count over 90 minutes (None if insufficient sample)."""
    if not _safe(minutes) or minutes <= 300:
        return None
    if not _safe(raw):
        return None
    return round(raw * 90.0 / minutes, 3)


def percentile(value: float | None, cohort_values: list) -> float | None:
    """Share of the position cohort <= value (0..1). Lower=worse for most
    metrics. None if the metric is unavailable."""
    if not _safe(value):
        return None
    below = sum(1 for v in cohort_values if v is not None and _safe(v) and v <= value)  # type: ignore[arg-type]
    total = max(1, len(cohort_values))
    return round(below / total, 4)


def composite_score(metrics: list[MetricValue], position: str) -> float | None:
    """Weighted mean of position percentiles -> 0..100."""
    weights = POSITION_WEIGHTS.get(position)
    if not weights:
        return None
    weighted = 0.0
    weight_total = 0.0
    scored_metrics = {m.name: m for m in metrics}
    for name, (w, higher_better) in weights.items():
        m = scored_metrics.get(name)
        if m is None or m.percentile is None:
            continue
        val = m.percentile if higher_better else 1.0 - m.percentile
        weighted += w * val
        weight_total += w
    if weight_total <= 0:
        return None
    # Normalise borrow: if some weights unused, rescale to the used weights.
    return round(100.0 * weighted / weight_total, 1)


def estimate_market_value(score: float | None, position: str, age: int | None) -> int | None:
    """Heuristic EUR value: score^3 * position pay * age discount."""
    if score is None:
        return None
    pay = POSITION_PAY.get(position, 1.0)
    if age is not None:
        if age <= 21:
            age_factor = 1.3
        elif age >= 30:
            age_factor = max(0.35, 1.0 - (age - 29) * 0.08)
        else:
            age_factor = 1.0
    else:
        age_factor = 1.0
    base = 1250  # EUR / (score^3)
    return int(round(base * (score / 50.0) ** 3 * pay * age_factor / 10) * 10)

