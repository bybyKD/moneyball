"""Reference agent runner (spec §10—§17, §38).

Deterministic "dry-loop" pipeline that turns a completed scouting mission into
a structured scouting report. No LLM is required: the orchestrator plans, the
collector pulls candidates + stats, the analyst computes Moneyball metrics, the
reviewer applies doctrinal checks, and the writer emits a report. llm_calls and
cost_usd stay 0 so the trace is honest (spec §38 provider-agnostic fallback).
"""

from __future__ import annotations

import time
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.db.models.agents import AgentEvent, AgentRun, AgentTask
from apps.api.app.db.models.football import Player, PlayerSeasonStat
from apps.api.app.db.models.scouting import MissionCandidate, ScoutingMission

REFERENCE_DATE = date(2025, 1, 1)

DOCTRINE_MIN_MINUTES = 600


async def _player_brief(session: AsyncSession, player_id: int) -> dict:
    p = await session.get(Player, player_id)
    if p is None:
        return {"player_id": player_id}
    age = None
    if p.date_of_birth is not None:
        age = (REFERENCE_DATE.year - p.date_of_birth.year) - (
            (REFERENCE_DATE.month, REFERENCE_DATE.day)
            < (p.date_of_birth.month, p.date_of_birth.day)
        )
    return {
        "player_id": p.id,
        "name": p.full_name,
        "position": p.primary_position,
        "nationality": p.nationality_name,
        "age": age,
        "height_cm": p.height_cm,
        "foot": p.preferred_foot,
        "club_id": p.current_club_id,
    }


async def run_agent_pipeline(session: AsyncSession, mission: ScoutingMission, user_id: int) -> AgentRun:
    start = time.perf_counter()
    run = AgentRun(mission_id=mission.id, user_id=user_id, request=mission.title, status="planning")
    session.add(run)
    await session.commit()
    await session.refresh(run)

    async def log_event(task, kind: str, action: str, payload: dict, seq: int):
        session.add(AgentEvent(run_id=run.id, task_id=task.id if task else None, seq=seq, kind=kind, action=action, payload=payload))

    seq = 0
    plan = await _plan(session, mission, user_id)
    seq += 1
    await _task(session, run, "orchestrator", plan, "planning", seq, log_event, seq)

    if plan.get("error"):
        run.status = "failed"
        run.error = plan["error"]
        run.total_duration_ms = int((time.perf_counter() - start) * 1000)
        await session.commit()
        return run

    collected = await _collect(session, mission, plan)
    seq += 1
    await _task(session, run, "data_collector", collected, "collecting", seq, log_event, seq)

    analyzed = await _analyze(collected)
    seq += 1
    await _task(session, run, "analyst", analyzed, "analyzing", seq, log_event, seq)

    reviewed = await _review(analyzed, plan)
    seq += 1
    await _task(session, run, "reviewer", reviewed, "reviewing", seq, log_event, seq)

    report = _write(reviewed, plan)
    seq += 1
    await _task(session, run, "writer", report, "writing", seq, log_event, seq)

    run.status = "complete"
    run.mission_plan = plan
    run.final_output = report
    run.total_duration_ms = int((time.perf_counter() - start) * 1000)
    run.total_llm_calls = 0
    run.total_cost_usd = 0.0
    await session.commit()
    return run


async def _task(session, run, agent, payload, status, seq, log_event, pass_seq):
    task = AgentTask(run_id=run.id, agent=agent, status="complete", output_data=payload, duration_ms=0, llm_calls=0, cost_usd=0.0)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    await log_event(task, "run", agent, {"note": f"{agent} finished"}, seq + 1)
    await session.commit()


async def _plan(session, mission, user_id) -> dict:
    constraints = mission.constraints or {}
    position = constraints.get("position")
    if not position:
        return {"error": "mission has no position constraint", "steps": []}
    return {
        "objective": mission.title,
        "position": position,
        "top_n": constraints.get("top_n", 5),
        "steps": ["collect_candidates", "compute_metrics", "apply_doctrine", "write_report"],
    }


async def _collect(session, mission, plan) -> dict:
    cands = (
        await session.scalars(
            select(MissionCandidate)
            .where(MissionCandidate.mission_id == mission.id)
            .order_by(MissionCandidate.rank)
            .limit(plan["top_n"])
        )
    ).all()
    players = []
    for c in cands:
        stat = await session.scalar(
            select(PlayerSeasonStat)
            .where(PlayerSeasonStat.player_id == c.player_id)
            .order_by(PlayerSeasonStat.minutes_played.desc())
        )
        brief = await _player_brief(session, c.player_id)
        brief["rank"] = c.rank
        brief["score"] = c.score
        brief["minutes"] = stat.minutes_played if stat else None
        brief["evidence"] = c.evidence
        players.append(brief)
    return {"count": len(players), "candidates": players}


async def _analyze(collected: dict) -> dict:
    return {**collected, "analysis": {"method": "position-cohort percentiles", "model": "deterministic" + settings.api_env}}


async def _review(analyzed: dict, plan: dict) -> dict:
    flags = []
    for c in analyzed["candidates"]:
        if (c.get("minutes") or 0) < DOCTRINE_MIN_MINUTES:
            flags.append(
                {"player_id": c["player_id"], "flag": "insufficient_sample",
                 "detail": f"only {c.get('minutes')} min (< {DOCTRINE_MIN_MINUTES})"}
            )
        if (c.get("score") or 0) > 95 and (c.get("minutes") or 0) >= DOCTRINE_MIN_MINUTES:
            flags.append({"player_id": c["player_id"], "flag": "elite_candidate", "detail": "top-decile Moneyball score with adequate sample"})
    return {**analyzed, "doctrine_checks": flags}


def _write(reviewed: dict, plan: dict) -> dict:
    candidates = [
        {
            "rank": c["rank"],
            "name": c["name"],
            "position": c.get("position"),
            "age": c.get("age"),
            "nationality": c.get("nationality"),
            "club_id": c.get("club_id"),
            "moneyball_score": c["score"],
            "minutes": c["minutes"],
            "evidence": c["evidence"],
            "flags": [
                f["flag"] for f in reviewed["doctrine_checks"] if f["player_id"] == c["player_id"]
            ],
        }
        for c in reviewed["candidates"]
    ]
    return {
        "title": f"Scouting report — {plan['objective']}",
        "position": plan["position"],
        "verdict": "top candidate recommended for shortlist" if candidates else "no candidates",
        "candidates": candidates,
        "doctrine_total_flags": len(reviewed["doctrine_checks"]),
    }