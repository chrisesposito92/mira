"""RAG retrieval tool for injecting context into agent prompts."""

import logging
from uuid import UUID

from langgraph.store.base import BaseStore

from app.db.client import get_db_pool
from app.rag.retriever import RetrievedChunk, retrieve

logger = logging.getLogger(__name__)


async def rag_retrieve(
    query: str,
    project_id: str | None = None,
    k: int = 5,
    store: BaseStore | None = None,
) -> str:
    """Retrieve and format RAG context as a string for injection into prompts."""
    pool = await get_db_pool()
    # Fetch 2x candidates when store available for re-ranking
    fetch_k = k * 2 if store and project_id else k
    chunks = await retrieve(pool, query, UUID(project_id) if project_id else None, fetch_k)

    if store and project_id and chunks:
        from app.agents.memory_rag import rerank_with_feedback, retrieve_rag_feedback

        try:
            feedback = await retrieve_rag_feedback(store, project_id)
            if feedback:
                chunks = rerank_with_feedback(chunks, feedback)
        except Exception:
            logger.warning("RAG feedback re-ranking failed, using default order", exc_info=True)

    return format_chunks(chunks[:k])


def format_chunks(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into a readable string."""
    if not chunks:
        return "No relevant documentation found."
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("source", chunk.source_type)
        header = f"--- Source {i} ({source}, relevance: {chunk.score:.2f}) ---"
        parts.append(f"{header}\n{chunk.content}")
    return "\n\n".join(parts)
