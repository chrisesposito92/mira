"""RAG feedback memory — tracks which RAG chunks lead to good/bad entity outcomes."""

import hashlib
import logging
import re

from langgraph.store.base import BaseStore

from app.rag.retriever import RetrievedChunk

logger = logging.getLogger(__name__)


def _hash_chunk(content: str) -> str:
    """Create a stable hash for chunk identification."""
    return hashlib.sha256(content.strip().encode()).hexdigest()[:16]


def _parse_rag_chunks(rag_context: str) -> list[dict]:
    """Parse formatted RAG text from format_chunks() output.

    Expected format:
        --- Source 1 (source_name, relevance: 0.85) ---
        chunk content here...

        --- Source 2 (another_source, relevance: 0.72) ---
        more chunk content...
    """
    try:
        header_pattern = re.compile(r"---\s*Source\s+\d+\s*\(.*?,\s*relevance:\s*([\d.]+)\)\s*---")
        headers = list(header_pattern.finditer(rag_context))

        if not headers:
            return []

        chunks = []
        for i, match in enumerate(headers):
            score = float(match.group(1))
            start = match.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(rag_context)
            content = rag_context[start:end].strip()
            if content:
                chunks.append(
                    {
                        "content": content,
                        "hash": _hash_chunk(content),
                        "score": score,
                    }
                )
        return chunks
    except Exception:
        logger.warning("Failed to parse RAG chunks from context")
        return []


def _compute_approval_signal(decisions: list[dict]) -> float:
    """Compute aggregate approval signal from decisions.

    Score mapping: approve=1.0, edit=0.5, reject=0.0.
    Returns average score, defaulting to 0.5 if no decisions.
    """
    if not decisions:
        return 0.5

    score_map = {"approve": 1.0, "edit": 0.5, "reject": 0.0}
    scores = [score_map.get(d.get("action", ""), 0.5) for d in decisions]
    return sum(scores) / len(scores)


async def record_rag_feedback(
    store: BaseStore,
    project_id: str,
    entity_type: str,
    rag_context: str,
    decisions: list[dict],
) -> None:
    """Record feedback on RAG chunks based on user approval decisions.

    Uses exponential moving average (alpha=0.3) to update chunk scores.
    """
    try:
        chunks = _parse_rag_chunks(rag_context)
        if not chunks:
            return

        signal = _compute_approval_signal(decisions)
        namespace = ("project", project_id, "rag_feedback")
        alpha = 0.3

        for chunk in chunks:
            chunk_hash = chunk["hash"]
            # Key includes entity_type to prevent cross-entity-type signal overwriting.
            # A chunk approved for "product" and rejected for "pricing" gets separate entries.
            key = f"{chunk_hash}_{entity_type}"
            existing = await store.aget(namespace, key)

            if existing and existing.value:
                old_score = existing.value.get("score", 0.5)
                old_count = existing.value.get("count", 0)
                new_score = alpha * signal + (1 - alpha) * old_score
                new_count = old_count + 1
            else:
                new_score = signal
                new_count = 1

            await store.aput(
                namespace,
                key,
                {
                    "chunk_hash": chunk_hash,
                    "entity_type": entity_type,
                    "score": new_score,
                    "count": new_count,
                    "last_signal": signal,
                },
            )
    except Exception:
        logger.warning("Failed to record RAG feedback for project %s", project_id)


async def retrieve_rag_feedback(store: BaseStore, project_id: str) -> dict[str, float]:
    """Read all RAG feedback scores for a project.

    Feedback is stored per entity_type, so multiple entries may exist for the
    same chunk. Scores are averaged across entity types to produce a single
    blended score per chunk for re-ranking.

    Returns: {chunk_hash: score} dict.
    """
    try:
        namespace = ("project", project_id, "rag_feedback")
        items = await store.asearch(namespace, limit=500)
        # Group by raw chunk_hash (entries may be keyed as "hash_entitytype")
        scores: dict[str, list[float]] = {}
        for item in items:
            if not item.value:
                continue
            chunk_hash = item.value.get("chunk_hash", item.key)
            score = item.value.get("score", 0.5)
            scores.setdefault(chunk_hash, []).append(score)
        return {h: sum(s) / len(s) for h, s in scores.items()}
    except Exception:
        logger.warning("Failed to retrieve RAG feedback for project %s", project_id)
        return {}


def rerank_with_feedback(chunks: list[RetrievedChunk], feedback: dict[str, float]) -> list:
    """Re-rank chunks using blended score of retrieval relevance and feedback.

    Blended score: 0.7 * chunk.score + 0.3 * feedback.get(hash, 0.5)
    """

    def blended_score(chunk: RetrievedChunk) -> float:
        chunk_hash = _hash_chunk(chunk.content)
        feedback_score = feedback.get(chunk_hash, 0.5)
        return 0.7 * chunk.score + 0.3 * feedback_score

    return sorted(chunks, key=blended_score, reverse=True)
