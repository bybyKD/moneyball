"""Similar-players route (spec §24 semantic search).

GET /api/players/{player_id}/similar?k=6
    pgvector L2 nearest-neighbors over the deterministic tactical_profile
    embedding (moneyball_v1). Shares the HNSW index; distances map to
    cosine similarity because vectors are unit-normalized.
"""


from apps.api.app.core.config import settings
from apps.api.app.core.errors import NotFoundError
from apps.api.app.db.models.embeddings import PlayerEmbedding
from apps.api.app.db.models.football import Player
from apps.api.app.db.session import get_session
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/players", tags=["semantic"])


@router.get("/{player_id}/similar")
async def similar_players(
    player_id: int,
    k: int = 6,
    provider: str | None = Query(default=None, description="data provider (default: configured default)"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    provider = provider or settings.default_provider
    k = max(1, min(k, 20))
    target_emb = await session.scalar(
        select(PlayerEmbedding).where(
            PlayerEmbedding.player_id == player_id,
            PlayerEmbedding.provider == provider,
        )
    )
    if target_emb is None or target_emb.embedding is None:
        raise NotFoundError("No embedding for this player; run `make embed` first")

    rows = (
        await session.execute(
            select(PlayerEmbedding, PlayerEmbedding.embedding.l2_distance(target_emb.embedding).label("dist"))
            .where(
                PlayerEmbedding.player_id != player_id,
                PlayerEmbedding.provider == provider,
                PlayerEmbedding.embedding.isnot(None),
            )
            .order_by("dist")
            .limit(k)
        )
    ).all()

    player_ids = [emb.player_id for emb, _ in rows]
    players = {
        p.id: p
        for p in (await session.scalars(select(Player).where(Player.id.in_(player_ids)))).all()
    }

    results = []
    for emb, dist in rows:
        p = players.get(emb.player_id)
        # cosine sim from L2 on unit vectors: cos = 1 - d^2/2 (clamp for float noise)
        sim = max(-1.0, min(1.0, 1.0 - (float(dist) ** 2) / 2.0))
        results.append(
            {
                "player_id": emb.player_id,
                "name": p.full_name if p else None,
                "position": p.primary_position if p else None,
                "similarity": round(sim, 4),
                "model": emb.model,
            }
        )
    return {"player_id": player_id, "model": target_emb.model, "kind": target_emb.kind, "neighbors": results}
