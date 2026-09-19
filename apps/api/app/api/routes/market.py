"""Market routes (spec §22).

GET /api/market/value-picks?position=ST&min_minutes=600&k=10
    rank the roster by Moneyball performance per estimated market euro.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.session import get_session
from apps.api.app.services.market import value_ranking

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/value-picks")
async def value_picks(
    position: str | None = Query(default=None, description="position filter (GK/CB/FB/DM/CM/AM/W/ST); all if omitted"),
    min_minutes: int = Query(default=600, ge=0),
    k: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> dict:
    rows = await value_ranking(session, position=position, min_minutes=min_minutes, k=k)
    return {
        "method": "score / ln(value_eur+1) · production-per-euro",
        "position": position or "all",
        "count": len(rows),
        "picks": rows,
    }