"""Model registry — import every model so Alembic autogenerate sees them."""

from apps.api.app.db.models.agents import AgentEvent, AgentRun, AgentTask
from apps.api.app.db.models.auth import User
from apps.api.app.db.models.embeddings import PlayerEmbedding
from apps.api.app.db.models.football import (
    Club,
    Competition,
    League,
    Player,
    PlayerMatchStat,
    PlayerPosition,
    PlayerRole,
    PlayerSeasonStat,
    Season,
)
from apps.api.app.db.models.market import (
    Contract,
    Injury,
    MarketValue,
    Source,
    Transfer,
)
from apps.api.app.db.models.scouting import (
    MissionCandidate,
    PlayerComparison,
    ScoutingMission,
    ScoutingReport,
    Shortlist,
    ShortlistPlayer,
)

__all__ = [
    "AgentEvent",
    "AgentRun",
    "AgentTask",
    "Club",
    "Competition",
    "Contract",
    "Injury",
    "League",
    "MarketValue",
    "MissionCandidate",
    "Player",
    "PlayerComparison",
    "PlayerEmbedding",
    "PlayerMatchStat",
    "PlayerPosition",
    "PlayerRole",
    "PlayerSeasonStat",
    "ScoutingMission",
    "ScoutingReport",
    "Season",
    "Shortlist",
    "ShortlistPlayer",
    "Source",
    "Transfer",
    "User",
]