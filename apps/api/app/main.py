"""FastAPI application factory — wired per spec §26–28, §36–37, §45-B.

Startup sequence:
  1. load settings (validated pydantic)
  2. startup: ping DB (fail fast), init pgvector-backed services
  3. mount middleware (CORS, request context, error handlers, structured logging)
  4. mount routers (health, auth, users, players stubs → full in later phases)
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from apps.api.app.core.config import settings
from apps.api.app.core.errors import register_exception_handlers
from apps.api.app.core.logging import configure_logging, emit
from apps.api.app.api.router import api_router
from apps.api.app.db.session import engine


async def check_database_ready() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.api_log_level)
    emit("api.startup", "starting", env=settings.api_env, version=settings.api_version)
    await check_database_ready()
    emit("api.startup", "database ready")
    yield
    await engine.dispose()
    emit("api.shutdown", "bye")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Moneyball API",
        version=settings.api_version,
        description="Moneyball AI scouting platform — backend (spec §26).",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_root_path)

    return app


app = create_app()