"""Scouting workspace models: missions, candidates, shortlists, comparisons,
reports (spec §19–21)."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.db.base import Base, TimestampMixin


class ScoutingMission(Base, TimestampMixin):
    __tablename__ = "scouting_missions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    query_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # original NL request
    constraints: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # §15 structured constraints
    weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # §11 configurable model weights
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    # draft | active | running | completed | failed | archived
    results_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class MissionCandidate(Base, TimestampMixin):
    __tablename__ = "mission_candidates"
    __table_args__ = (UniqueConstraint("mission_id", "player_id", name="uq_mission_candidate"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("scouting_missions.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # §12 explanation
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="candidate")


class Shortlist(Base, TimestampMixin):
    __tablename__ = "shortlists"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ShortlistPlayer(Base, TimestampMixin):
    __tablename__ = "shortlist_players"
    __table_args__ = (UniqueConstraint("shortlist_id", "player_id", name="uq_shortlist_player"), Index("ix_sp_status", "status"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    shortlist_id: Mapped[int] = mapped_column(ForeignKey("shortlists.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DISCOVERED"
    )  # DISCOVERED|RESEARCHING|WATCHLIST|SHORTLISTED|SCOUTED|CONTACTED|REJECTED|SIGNED
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PlayerComparison(Base, TimestampMixin):
    __tablename__ = "player_comparisons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    player_ids: Mapped[list] = mapped_column(JSON, nullable=False)  # ordered list of player ids
    custom_weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # §29 custom metric weighting
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ScoutingReport(Base, TimestampMixin):
    __tablename__ = "scouting_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    mission_id: Mapped[int | None] = mapped_column(ForeignKey("scouting_missions.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[dict] = mapped_column(JSON, nullable=False)  # §21 structured sections
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending | approved | flagged
    confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)  # HIGH|MEDIUM|LOW
    format_type: Mapped[str] = mapped_column(String(10), nullable=False, default="markdown")
    source_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)