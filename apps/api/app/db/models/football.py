"""Football domain models: leagues, competitions, seasons, clubs, players,
player positions/roles, and per-season/per-match statistics."""

from apps.api.app.db.base import Base, TimestampMixin
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class League(Base, TimestampMixin):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    country_name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    strength_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="demo")


class Competition(Base, TimestampMixin):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False, default="league")  # league|cup|international
    gender: Mapped[str] = mapped_column(String(12), nullable=False, default="male")
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="demo", index=True)
    provider_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)


class Season(Base, TimestampMixin):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # e.g. "2024/2025"
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="demo", index=True)
    provider_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)


class Club(Base, TimestampMixin):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    country_name: Mapped[str] = mapped_column(String(120), nullable=False)
    league_id: Mapped[int | None] = mapped_column(ForeignKey("leagues.id"), nullable=True, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="demo", index=True)
    provider_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)


class Player(Base, TimestampMixin):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    date_of_birth: Mapped[Date | None] = mapped_column(Date, nullable=True, index=True)
    nationality_code: Mapped[str | None] = mapped_column(String(3), nullable=True, index=True)
    nationality_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_foot: Mapped[str] = mapped_column(String(10), nullable=True)  # left|right|both
    primary_position: Mapped[str] = mapped_column(String(8), nullable=False, index=True)  # GK|CB|FB|DM|CM|AM|W|ST
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    current_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="demo", index=True)
    provider_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class PlayerPosition(Base, TimestampMixin):
    __tablename__ = "player_positions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(8), nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class PlayerRole(Base, TimestampMixin):
    __tablename__ = "player_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(60), nullable=False)  # tactical role e.g. "deep_lying_playmaker"
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)


class PlayerSeasonStat(Base, TimestampMixin):
    __tablename__ = "player_season_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "season_id", "competition_id", name="uq_pss_player_season_comp"),
        Index("ix_pss_value_lookup", "position", "minutes_played"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False, index=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), nullable=False, index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"), nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(8), nullable=False, index=True)

    # playing time
    minutes_played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    appearances: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # attacking
    goals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    penalty_goals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shots_on_target: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    npxg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    xa: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    touches_in_box: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shot_creating_actions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    goal_creating_actions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # passing
    passes_attempted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passes_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progressive_passes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    key_passes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    final_third_passes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passes_into_box: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    through_balls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    long_passes_attempted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    long_passes_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progressive_passing_distance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # possession / carrying
    carries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progressive_carries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    carries_into_box: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    carries_into_final_third: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    carry_distance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progressive_carry_distance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_dribbles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dribbles_attempted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    miscontrols: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dispossessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    touches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # defending
    tackles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interceptions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    blocks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clearances: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    defensive_duels_won: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    defensive_duels_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aerial_duels_won: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aerial_duels_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pressures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pressures_successful: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ball_recoveries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # cards
    yellow_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    red_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="demo", index=True)

    player = relationship("Player")
    season = relationship("Season")


class PlayerMatchStat(Base, TimestampMixin):
    __tablename__ = "player_match_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "season_id", "competition_id", "match_date", name="uq_pms_player_match"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False, index=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), nullable=False, index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"), nullable=False, index=True)
    opponent_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True)
    match_date: Mapped[Date] = mapped_column(Date, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    goals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    xa: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
