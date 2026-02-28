"""RAG retrieval tool for injecting context into agent prompts."""

from uuid import UUID

from app.db.client import get_db_pool
from app.rag.retriever import RetrievedChunk, retrieve


async def rag_retrieve(query: str, project_id: str | None = None, k: int = 5) -> str:
    """Retrieve and format RAG context as a string for injection into prompts."""
    pool = await get_db_pool()
    chunks = await retrieve(pool, query, UUID(project_id) if project_id else None, k)
    return format_chunks(chunks)


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
