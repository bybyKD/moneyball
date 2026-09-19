"""Market & context models: transfers, market values, contracts, injuries,
sources (spec §22, §35 — every data point carries source + season)."""

from apps.api.app.db.base import Base, TimestampMixin
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)  # demo|statsbomb|transfermarkt|news...
    kind: Mapped[str] = mapped_column(String(40), nullable=False, default="dataset")  # dataset|news|report|official
    url: Mapped[str | None] = mapped_column(String(600), nullable=True)
    attribution_required: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_updated: Mapped[Date | None] = mapped_column(Date, nullable=True)


class Transfer(Base, TimestampMixin):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    from_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True)
    to_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True)
    transfer_date: Mapped[Date] = mapped_column(Date, nullable=False)
    fee_eur: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # null = free transfer
    reported_fee: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_rumored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)


class MarketValue(Base, TimestampMixin):
    __tablename__ = "market_values"
    __table_args__ = (Index("ix_mv_lookup", "player_id", "date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    value_eur: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    is_estimate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True)
    start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    weekly_wages_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clauses: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)


class Injury(Base, TimestampMixin):
    __tablename__ = "injuries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    injury_type: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    days_missed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matches_missed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
