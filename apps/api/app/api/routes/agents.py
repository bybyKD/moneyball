"""Agent routes (spec §17, §24).

POST /api/agents/runs        run the reference pipeline for a completed mission
GET  /api/agents/runs        list my runs
GET  /api/agents/runs/{id}   run + task trace + events
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.deps import CurrentUser
from apps.api.app.core.errors import NotFoundError
from apps.api.app.db.models.agents import AgentEvent, AgentRun, AgentTask
from apps.api.app.db.models.scouting import ScoutingMission
from apps.api.app.db.session import get_session
from apps.api.app.services.agents import run_agent_pipeline

router = APIRouter(prefix="/agents/runs")


class RunIn(BaseModel):
    mission_id: int


@router.post("", response_model=dict, status_code=201)
async def create_run(body: RunIn, user: CurrentUser, session: AsyncSession = Depends(get_session)):
    mission = await session.get(ScoutingMission, body.mission_id)
    if mission is None or mission.user_id != user.id:
        raise NotFoundError("Mission not found")
    if mission.status != "complete":
        raise NotFoundError("Mission not complete; run it first")
    run = await run_agent_pipeline(session, mission, user.id)
    return {
        "id": run.id,
        "status": run.status,
        "report": run.final_output,
        "llm_calls": run.total_llm_calls,
        "cost_usd": run.total_cost_usd,
    }


@router.get("", response_model=list[dict])
async def list_runs(user: CurrentUser, session: AsyncSession = Depends(get_session)):
    runs = (
        await session.scalars(select(AgentRun).where(AgentRun.user_id == user.id).order_by(AgentRun.id.desc()))
    ).all()
    return [{"id": r.id, "mission_id": r.mission_id, "request": r.request, "status": r.status, "llm_calls": r.total_llm_calls} for r in runs]


@router.get("/{run_id}", response_model=dict)
async def get_run(run_id: int, user: CurrentUser, session: AsyncSession = Depends(get_session)):
    run = await session.get(AgentRun, run_id)
    if run is None or run.user_id != user.id:
        raise NotFoundError("Run not found")
    tasks = (
        await session.scalars(select(AgentTask).where(AgentTask.run_id == run.id).order_by(AgentTask.id))
    ).all()
    events = (
        await session.scalars(select(AgentEvent).where(AgentEvent.run_id == run.id).order_by(AgentEvent.seq))
    ).all()
    return {
        "id": run.id,
        "status": run.status,
        "request": run.request,
        "plan": run.mission_plan,
        "report": run.final_output,
        "duration_ms": run.total_duration_ms,
        "llm_calls": run.total_llm_calls,
        "cost_usd": run.total_cost_usd,
        "tasks": [
            {"agent": t.agent, "status": t.status, "note": t.note, "output": t.output_data} for t in tasks
        ],
        "events": [{"seq": e.seq, "agent": e.action, "kind": e.kind, "payload": e.payload} for e in events],
    }