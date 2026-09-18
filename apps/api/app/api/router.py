"""API Router — registers sub-routers (spec §26/§28)."""

from fastapi import APIRouter


api_router = APIRouter()

# Local imports keep router.py dependency-light at import time.
from apps.api.app.api.routes import analytics, auth, health, players, users  # noqa: E402

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(players.router)
api_router.include_router(analytics.router)