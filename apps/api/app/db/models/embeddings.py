"""Embeddings model (spec §24) — pgvector-backed semantic vectors.

Used for semantic retrieval over player descriptions, tactical profiles,
reports, and research documents. Structured statistics remain in SQL.
"""

from pgvector.sqlalchemy import Vector

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.config import settings
from apps.api.app.db.base import Base, TimestampMixin

_description_index = Index(
    "ix_pe_vector",
    "embedding",
    postgresql_using="hnsw",
    postgresql_ops={"embedding": "vector_l2_ops"},
)


class PlayerEmbedding(Base, TimestampMixin):
    __tablename__ = "player_embeddings"
    __table_args__ = (_description_index,)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False, default="tactical_profile")
    # tactical_profile | description | report | news
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[Vector] = mapped_column(Vector(settings.embedding_dim), nullable=True)
    model: Mapped[str] = mapped_column(String(80), nullable=False, default="none")