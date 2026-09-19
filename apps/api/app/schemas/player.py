"""Player response schemas (spec §7). Matches the players table now; advanced
per-90 / percentile fields arrive with the analytics phases."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    full_name: str
    date_of_birth: date | None = None
    nationality_code: str | None = None
    nationality_name: str | None = None
    height_cm: int | None
    preferred_foot: str | None
    primary_position: str
    current_club_id: int | None
    provider: str = "demo"
