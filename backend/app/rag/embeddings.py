"""OpenAI embedding generation for RAG pipeline."""

import openai

from app.config import settings


async def embed_texts(
    texts: list[str],
    model: str | None = None,
    batch_size: int | None = None,
) -> list[list[float]]:
    """Embed multiple texts, batching to stay within API limits.

    Returns list of embedding vectors (1536 dimensions for text-embedding-3-small).
    """
    if not texts:
        return []

    model = model or settings.embedding_model
    batch_size = batch_size or settings.embedding_batch_size
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = await client.embeddings.create(input=batch, model=model)
        all_embeddings.extend([item.embedding for item in response.data])

    return all_embeddings


async def embed_single(text: str, model: str | None = None) -> list[float]:
    """Embed a single text string. Convenience wrapper around embed_texts."""
    results = await embed_texts([text], model=model)
    return results[0]
