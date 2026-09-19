"""Async engine + session factory.

Uses psycopg (v3) async. Test override support via ``override_engine``.
"""

from collections.abc import AsyncIterator

from apps.api.app.core.config import settings
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(url: str | None = None, *, force_dispose: bool = False) -> AsyncEngine:
    return create_async_engine(
        url or settings.database_url,
        echo=False,
        pool_pre_ping=True,
        poolclass=NullPool if force_dispose else None,
    )


engine = build_engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
