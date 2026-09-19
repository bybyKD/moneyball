"""Comparison routes (spec §20, §24).

GET  /api/compare?player_a=A&player_b=B   stateless head-to-head
POST /api/compare  {player_ids:[A,B]}     auth-required, persists a
                                            PlayerComparison row (§20 replay)
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.deps import CurrentUser
from apps.api.app.core.errors import NotFoundError
from apps.api.app.db.models.scouting import PlayerComparison
from apps.api.app.db.session import get_session
from apps.api.app.services.comparison import compare_players

router = APIRouter(prefix="/compare")


class CompareIn(BaseModel):
    player_ids: list[int]
    name: str | None = None


@router.get("")
async def compare_get(
    player_a: int = Query(...),
    player_b: int = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await compare_players(session, [player_a, player_b])


@router.post("", status_code=201)
async def compare_post(
    body: CompareIn,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if len(body.player_ids) < 2:
        raise NotFoundError("Provide at least two player ids")
    result = await compare_players(session, body.player_ids[:5])
    comparison = PlayerComparison(
        user_id=user.id,
        name=body.name,
        player_ids=body.player_ids[:5],
        result=result,
    )
    session.add(comparison)
    await session.commit()
    await session.refresh(comparison)
    return {"id": comparison.id, "result": result}