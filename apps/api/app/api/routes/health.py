"""Health-check routes (spec §26)."""

from apps.api.app.api.deps import SessionDep
from apps.api.app.core.config import settings
from fastapi import APIRouter
from sqlalchemy import text

router = APIRouter(prefix="/health", tags=["system"])


@router.get("")
async def health() -> dict:
    return {"status": "ok", "service": "moneyball", "version": settings.api_version}


@router.get("/ready")
async def ready(session: SessionDep) -> dict:
    await session.execute(text("SELECT 1"))
    return {"status": "ready", "database": "up"}
