"""Embed the demo roster into pgvector (deterministic moneyball_demo_v1).

Run: python -m apps.api.app.scripts.embed_demo
"""

import asyncio

from apps.api.app.db.session import get_session
from apps.api.app.services.embeddings import build_all_embeddings


async def main() -> None:
    async for session in get_session():
        result = await build_all_embeddings(session)
        print(f"Done: embedded {result['embedded']} players ({result['model']}, dims={result['dims']})")


if __name__ == "__main__":
    asyncio.run(main())