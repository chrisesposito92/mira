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
CONCURRENCY = 5


async def _ingest_file(pool, json_file: Path, semaphore: asyncio.Semaphore) -> int:
    """Ingest a single JSON file with concurrency limiting."""
    async with semaphore:
        data = json.loads(json_file.read_text(encoding="utf-8"))
        metadata = {"title": data.get("title", ""), "source_url": data.get("url", "")}
        chunks = await ingest_document(
            pool,
            content=data["content"],
            source_type="m3ter_docs",
            metadata=metadata,
        )
        return chunks


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

    semaphore = asyncio.Semaphore(CONCURRENCY)
    total = len(json_files)
    completed = 0
    total_chunks = 0

    async def _ingest_and_track(json_file: Path) -> None:
        nonlocal completed, total_chunks
        chunks = await _ingest_file(pool, json_file, semaphore)
        total_chunks += chunks
        completed += 1
        if completed % 25 == 0 or completed == total:
            logger.info(
                "Progress: %d/%d files ingested (%d chunks)", completed, total, total_chunks
            )

    tasks = [_ingest_and_track(f) for f in json_files]
    await asyncio.gather(*tasks)

    await close_db_pool()
    logger.info("Done. Ingested %d total chunks from %d files", total_chunks, len(json_files))


if __name__ == "__main__":
    asyncio.run(main())
