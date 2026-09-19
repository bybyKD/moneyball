"""API Router — registers sub-routers (spec §26/§28)."""

from fastapi import APIRouter


api_router = APIRouter()

# Local imports keep router.py dependency-light at import time.
from apps.api.app.api.routes import agents, analytics, auth, health, market, players, scouting, similar, users  # noqa: E402

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(players.router)
api_router.include_router(analytics.router)
api_router.include_router(similar.router)
api_router.include_router(market.router)
api_router.include_router(scouting.router)
api_router.include_router(scouting.shortlist_router)
api_router.include_router(agents.router)