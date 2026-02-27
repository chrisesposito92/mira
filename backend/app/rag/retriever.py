"""Two-source retriever using pgvector cosine similarity."""

import json
import logging
from dataclasses import dataclass
from uuid import UUID

import asyncpg

from app.config import settings
from app.rag.embeddings import embed_single

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    content: str
    metadata: dict
    score: float
    source_type: str


async def retrieve(
    pool: asyncpg.Pool,
    query: str,
    project_id: UUID | None = None,
    k: int | None = None,
) -> list[RetrievedChunk]:
    """Retrieve top-k relevant chunks using two-source cosine similarity.

    Queries both m3ter_docs (global) and user_document (project-scoped),
    merges results by score, and returns top-k.
    """
    k = k or settings.retrieval_k
    query_embedding = await embed_single(query)
    embedding_str = str(query_embedding)

    results: list[RetrievedChunk] = []

    async with pool.acquire() as conn:
        # Source 1: m3ter docs (global, no project filter)
        m3ter_rows = await conn.fetch(
            """
            SELECT content, metadata, source_type,
                   1 - (embedding <=> $1) AS score
            FROM embeddings
            WHERE source_type = 'm3ter_docs'
            ORDER BY embedding <=> $1
            LIMIT $2
            """,
            embedding_str,
            k,
        )
        for row in m3ter_rows:
            results.append(
                RetrievedChunk(
                    content=row["content"],
                    metadata=(
                        json.loads(row["metadata"])
                        if isinstance(row["metadata"], str)
                        else row["metadata"]
                    ),
                    score=float(row["score"]),
                    source_type=row["source_type"],
                )
            )

        # Source 2: user documents (project-scoped)
        if project_id:
            user_rows = await conn.fetch(
                """
                SELECT content, metadata, source_type,
                       1 - (embedding <=> $1) AS score
                FROM embeddings
                WHERE source_type = 'user_document' AND project_id = $2
                ORDER BY embedding <=> $1
                LIMIT $3
                """,
                embedding_str,
                str(project_id),
                k,
            )
            for row in user_rows:
                results.append(
                    RetrievedChunk(
                        content=row["content"],
                        metadata=(
                            json.loads(row["metadata"])
                            if isinstance(row["metadata"], str)
                            else row["metadata"]
                        ),
                        score=float(row["score"]),
                        source_type=row["source_type"],
                    )
                )

    # Merge by score (descending) and return top-k
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:k]
