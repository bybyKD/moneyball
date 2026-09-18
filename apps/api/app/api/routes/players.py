"""Players API — read endpoints per spec §6/§7. Percentiles & per-90 merge in
Phase 3 (analytics engine); these routes expose raw repository rows."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.errors import NotFoundError
from apps.api.app.db.models.football import Player
from apps.api.app.db.session import get_session
from apps.api.app.schemas.player import PlayerOut

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[PlayerOut])
async def list_players(
    session: AsyncSession = Depends(get_session),
    position: str | None = None,
    league_id: int | None = None,
    age_max: int | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Player]:
    stmt = select(Player).order_by(Player.full_name).limit(min(limit, 200)).offset(max(offset, 0))
    if position:
        stmt = stmt.where(Player.primary_position == position)
    if q:
        stmt = stmt.where(Player.full_name.ilike(f"%{q}%"))
    rows = (await session.scalars(stmt)).all()
    return list(rows)


@router.get("/{player_id}", response_model=PlayerOut)
async def get_player(player_id: int, session: AsyncSession = Depends(get_session)) -> Player:
    player = await session.get(Player, player_id)
    if player is None:
        raise NotFoundError("Player not found")
    return player