"""Embedding ingestion pipeline — chunk, embed, store in pgvector."""

import json
import logging
from uuid import UUID

import asyncpg

from app.rag.chunker import chunk_text
from app.rag.embeddings import embed_texts

logger = logging.getLogger(__name__)


async def ingest_document(
    pool: asyncpg.Pool,
    content: str,
    source_type: str,
    metadata: dict | None = None,
    project_id: UUID | None = None,
    source_id: UUID | None = None,
    chunk_size: int = 4000,
    chunk_overlap: int = 200,
) -> int:
    """Chunk text, generate embeddings, and store in pgvector.

    Returns the number of chunks stored. Runs as an atomic transaction.
    """
    chunks = chunk_text(
        content, metadata=metadata, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    if not chunks:
        return 0

    texts = [c.content for c in chunks]
    embeddings = await embed_texts(texts)

    async with pool.acquire() as conn:
        async with conn.transaction():
            for chunk, embedding in zip(chunks, embeddings):
                await conn.execute(
                    """
                    INSERT INTO embeddings
                        (source_type, source_id, project_id, content, metadata, embedding)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    source_type,
                    str(source_id) if source_id else None,
                    str(project_id) if project_id else None,
                    chunk.content,
                    json.dumps(chunk.metadata),
                    str(embedding),
                )

    logger.info("Ingested %d chunks for source_type=%s", len(chunks), source_type)
    return len(chunks)


async def ingest_batch(
    pool: asyncpg.Pool,
    pages: list[dict],
    source_type: str,
) -> int:
    """Ingest multiple documents. Each page dict has 'content', 'title', 'url' keys.

    Returns total chunks stored.
    """
    total = 0
    for page in pages:
        metadata = {"title": page.get("title", ""), "source_url": page.get("url", "")}
        count = await ingest_document(pool, page["content"], source_type, metadata=metadata)
        total += count
    return total


async def delete_by_source_type(pool: asyncpg.Pool, source_type: str) -> int:
    """Delete all embeddings of a given source type. Returns count deleted."""
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM embeddings WHERE source_type = $1", source_type)
        count = int(result.split()[-1])
        logger.info("Deleted %d embeddings for source_type=%s", count, source_type)
        return count


async def delete_by_source_id(pool: asyncpg.Pool, source_id: UUID) -> int:
    """Delete all embeddings for a specific source document. Returns count deleted."""
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM embeddings WHERE source_id = $1", str(source_id))
        count = int(result.split()[-1])
        logger.info("Deleted %d embeddings for source_id=%s", count, source_id)
        return count
