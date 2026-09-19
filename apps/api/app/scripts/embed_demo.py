"""Embed the data provider's roster into pgvector (deterministic moneyball_v1).

Run: python -m apps.api.app.scripts.embed_demo [--provider statsbomb]
"""

import argparse
import asyncio

from apps.api.app.core.config import settings
from apps.api.app.db.session import get_session
from apps.api.app.services.embeddings import build_all_embeddings


async def main(provider: str) -> None:
    async for session in get_session():
        result = await build_all_embeddings(session, provider=provider)
        print(
            f"Done: embedded {result['embedded']} players "
            f"({result['model']}, provider={result['provider']}, dims={result['dims']})"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build deterministic embeddings")
    parser.add_argument("--provider", default=None, help="data provider (default: configured default)")
    args = parser.parse_args()
    asyncio.run(main(args.provider or settings.default_provider))
