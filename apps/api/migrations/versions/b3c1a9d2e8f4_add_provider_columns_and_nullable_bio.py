"""add provider columns and nullable bio

Revision ID: b3c1a9d2e8f4
Revises: 7c3be29972d5
Create Date: 2026-09-19 10:00:00.000000

Adds source-provider provenance (statsbomb|demo) so real StatsBomb rows can
coexist with the synthetic demo roster and cohorts never mix: provider columns
on competitions, seasons, clubs, players, player_season_stats,
player_embeddings; provider_id (the external key, e.g. StatsBomb ids) on the
entity tables. Player bio fields (DOB/nationality) become nullable because open
event data carries no bios — unknowns are flagged, never invented.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c1a9d2e8f4"
down_revision: Union[str, None] = "7c3be29972d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_provider_pair(table: str, with_idx: bool = True) -> None:
    op.add_column(table, sa.Column("provider", sa.String(length=40), nullable=False, server_default="demo"))
    op.add_column(table, sa.Column("provider_id", sa.String(length=120), nullable=True))
    if with_idx:
        op.create_index(op.f(f"ix_{table}_provider"), table, ["provider"], unique=False)
        op.create_index(
            f"uq_{table}_provider_id",
            table,
            ["provider", "provider_id"],
            unique=True,
            postgresql_where=sa.text("provider_id IS NOT NULL"),
        )


def upgrade() -> None:
    # Bio fields without open-data coverage become nullable.
    op.alter_column("players", "date_of_birth", existing_type=sa.Date(), nullable=True)
    op.alter_column("players", "nationality_code", existing_type=sa.String(length=3), nullable=True)
    op.alter_column("players", "nationality_name", existing_type=sa.String(length=120), nullable=True)

    # Provenance pair on entity tables.
    _add_provider_pair("competitions")
    _add_provider_pair("seasons")
    _add_provider_pair("clubs")
    _add_provider_pair("players")

    # Provenance on per-row tables (no external id; derived from the parent).
    op.add_column("player_season_stats", sa.Column("provider", sa.String(length=40), nullable=False, server_default="demo"))
    op.create_index(op.f("ix_player_season_stats_provider"), "player_season_stats", ["provider"], unique=False)
    op.add_column("player_embeddings", sa.Column("provider", sa.String(length=40), nullable=False, server_default="demo"))
    op.create_index(op.f("ix_player_embeddings_provider"), "player_embeddings", ["provider"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_player_embeddings_provider"), table_name="player_embeddings")
    op.drop_column("player_embeddings", "provider")
    op.drop_index(op.f("ix_player_season_stats_provider"), table_name="player_season_stats")
    op.drop_column("player_season_stats", "provider")

    for table in ("competitions", "seasons", "clubs", "players"):
        op.drop_index(f"uq_{table}_provider_id", table_name=table)
        op.drop_index(op.f(f"ix_{table}_provider"), table_name=table)
        op.drop_column(table, "provider_id")
        op.drop_column(table, "provider")

    op.alter_column("players", "date_of_birth", existing_type=sa.Date(), nullable=False)
    op.alter_column("players", "nationality_code", existing_type=sa.String(length=3), nullable=False)
    op.alter_column("players", "nationality_name", existing_type=sa.String(length=120), nullable=False)