"""Scouting routes (spec §13—§16).

POST /api/missions                       create + auto-run a scouting mission
GET  /api/missions                      list my missions
GET  /api/missions/{id}                 mission + ranked candidates
POST /api/shortlists                    create a shortlist
GET  /api/shortlists                    list my shortlists
GET  /api/shortlists/{id}               shortlist + players
POST /api/shortlists/{id}/players/{pid} add a candidate to a shortlist
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.errors import NotFoundError
from apps.api.app.db.models.scouting import (
    MissionCandidate,
    ScoutingMission,
    Shortlist,
    ShortlistPlayer,
)
from apps.api.app.db.session import get_session
from apps.api.app.api.deps import CurrentUser
from apps.api.app.services.scouting import run_mission

router = APIRouter(prefix="/missions")


class MissionIn(BaseModel):
    title: str
    position: str
    top_n: int = 50


class ShortlistIn(BaseModel):
    name: str
    description: str | None = None


@router.post("", response_model=dict, status_code=201)
async def create_mission(body: MissionIn, user: CurrentUser, session: AsyncSession = Depends(get_session)):
    mission = ScoutingMission(
        user_id=user.id,
        title=body.title,
        status="running",
        constraints={"position": body.position, "top_n": body.top_n},
    )
    session.add(mission)
    await session.commit()
    await session.refresh(mission)
    await run_mission(session, mission, body.position, body.top_n)
    mission.status = "complete"
    await session.commit()
    return {"id": mission.id, "status": mission.status, "position": body.position}


@router.get("", response_model=list[dict])
async def list_missions(user: CurrentUser, session: AsyncSession = Depends(get_session)):
    missions = (
        await session.scalars(
            select(ScoutingMission).where(ScoutingMission.user_id == user.id).order_by(ScoutingMission.id.desc())
        )
    ).all()
    return [{"id": m.id, "title": m.title, "status": m.status, "constraints": m.constraints} for m in missions]


@router.get("/{mission_id}", response_model=dict)
async def get_mission(mission_id: int, user: CurrentUser, session: AsyncSession = Depends(get_session)):
    mission = await session.get(ScoutingMission, mission_id)
    if mission is None or mission.user_id != user.id:
        raise NotFoundError("Mission not found")
    candidates = (
        await session.scalars(
            select(MissionCandidate)
            .where(MissionCandidate.mission_id == mission.id)
            .order_by(MissionCandidate.rank)
        )
    ).all()
    return {
        "id": mission.id,
        "title": mission.title,
        "status": mission.status,
        "constraints": mission.constraints,
        "candidates": [
            {
                "rank": c.rank,
                "player_id": c.player_id,
                "score": c.score,
                "evidence": c.evidence,
            }
            for c in candidates
        ],
    }


shortlist_router = APIRouter(prefix="/shortlists")


@shortlist_router.get("", response_model=list[dict])
async def list_shortlists(user: CurrentUser, session: AsyncSession = Depends(get_session)):
    rows = (
        await session.scalars(
            select(Shortlist).where(Shortlist.user_id == user.id).order_by(Shortlist.id.desc())
        )
    ).all()
    return [{"id": s.id, "name": s.name, "description": s.description} for s in rows]


@shortlist_router.post("", response_model=dict, status_code=201)
async def create_shortlist(body: ShortlistIn, user: CurrentUser, session: AsyncSession = Depends(get_session)):
    sl = Shortlist(user_id=user.id, name=body.name, description=body.description)
    session.add(sl)
    await session.commit()
    await session.refresh(sl)
    return {"id": sl.id, "name": sl.name}


@shortlist_router.get("/{shortlist_id}", response_model=dict)
async def get_shortlist(shortlist_id: int, user: CurrentUser, session: AsyncSession = Depends(get_session)):
    sl = await session.get(Shortlist, shortlist_id)
    if sl is None or sl.user_id != user.id:
        raise NotFoundError("Shortlist not found")
    players = (
        await session.scalars(
            select(ShortlistPlayer).where(ShortlistPlayer.shortlist_id == sl.id)
        )
    ).all()
    return {
        "id": sl.id,
        "name": sl.name,
        "description": sl.description,
        "players": [
            {"player_id": p.player_id, "status": p.status, "priority": p.priority, "notes": p.notes}
            for p in players
        ],
    }


@shortlist_router.post("/{shortlist_id}/players/{player_id}", response_model=dict, status_code=201)
async def add_to_shortlist(
    shortlist_id: int,
    player_id: int,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    sl = await session.get(Shortlist, shortlist_id)
    if sl is None or sl.user_id != user.id:
        raise NotFoundError("Shortlist not found")
    existing = await session.scalar(
        select(ShortlistPlayer).where(
            ShortlistPlayer.shortlist_id == shortlist_id,
            ShortlistPlayer.player_id == player_id,
        )
    )
    if existing is None:
        session.add(
            ShortlistPlayer(shortlist_id=shortlist_id, player_id=player_id, status="scouting")
        )
        await session.commit()
    return {"shortlist_id": shortlist_id, "player_id": player_id, "added": existing is None}