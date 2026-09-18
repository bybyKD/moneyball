"""Player response schemas (spec §7). Full advanced-metric fields arrive with
the analytics phases (per-90, percentile buckets); duration/sample fields are
already present so the UI can show Moneyball confidence from day one."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    slug: str
    age: int
    birth_date: datetime | None
    nationality: str
    primary_position: str
    preferred_foot: str | None
    height_cm: int | None
    club_name: str | None
    league_name: str | None
    market_value_eur: int | None
    value_trend: str | None  # rising | stable | falling | unknown
    updated_at: datetime | None