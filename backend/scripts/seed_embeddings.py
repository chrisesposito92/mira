"""Seed pgvector with m3ter documentation embeddings.

Prerequisites: Run scrape_m3ter_docs.py first to populate data/m3ter_docs/.
Usage: cd backend && python -m scripts.seed_embeddings
"""

import asyncio
import json
import logging
from pathlib import Path

from app.db.client import close_db_pool, get_db_pool
from app.rag.ingestion import delete_by_source_type, ingest_document

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/m3ter_docs")


async def main() -> None:
    if not DATA_DIR.exists():
        logger.error("Data directory %s not found. Run scrape_m3ter_docs.py first.", DATA_DIR)
        return

    json_files = sorted(DATA_DIR.glob("*.json"))
    if not json_files:
        logger.error("No JSON files found in %s", DATA_DIR)
        return

    pool = await get_db_pool()

    # Clear existing m3ter_docs embeddings for idempotency
    deleted = await delete_by_source_type(pool, "m3ter_docs")
    logger.info("Cleared %d existing m3ter_docs embeddings", deleted)

    total_chunks = 0
    for json_file in json_files:
        data = json.loads(json_file.read_text(encoding="utf-8"))
        metadata = {"title": data.get("title", ""), "source_url": data.get("url", "")}
        chunks = await ingest_document(
            pool,
            content=data["content"],
            source_type="m3ter_docs",
            metadata=metadata,
        )
        total_chunks += chunks
        logger.info("Ingested %s: %d chunks", json_file.name, chunks)

    await close_db_pool()
    logger.info("Done. Ingested %d total chunks from %d files", total_chunks, len(json_files))


if __name__ == "__main__":
    asyncio.run(main())
