"""Market routes (spec §22).

GET /api/market/value-picks?position=ST&min_minutes=600&k=10
    rank the roster by Moneyball performance per estimated market euro.
"""

from apps.api.app.db.session import get_session
from apps.api.app.services.market import value_ranking
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/value-picks")
async def value_picks(
    position: str | None = Query(default=None, description="position filter (GK/CB/FB/DM/CM/AM/W/ST); all if omitted"),
    min_minutes: int = Query(default=600, ge=0),
    k: int = Query(default=10, ge=1, le=50),
    provider: str | None = Query(default=None, description="data provider (default: configured default)"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    rows = await value_ranking(session, position=position, min_minutes=min_minutes, k=k, provider=provider)
    return {
        "method": "score / ln(value_eur+1) · production-per-euro",
        "position": position or "all",
        "count": len(rows),
        "picks": rows,
    }


@router.get("/position-summary")
async def position_summary(min_minutes: int = 600, provider: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    from apps.api.app.services.market import position_summary as _summary

    return await _summary(session, min_minutes, provider=provider)
