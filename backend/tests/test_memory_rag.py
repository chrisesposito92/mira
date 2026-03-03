"""Tests for RAG feedback memory (app.agents.memory_rag)."""

from dataclasses import dataclass

import pytest
from langgraph.store.memory import InMemoryStore

from app.agents.memory_rag import (
    _compute_approval_signal,
    _hash_chunk,
    _parse_rag_chunks,
    record_rag_feedback,
    rerank_with_feedback,
    retrieve_rag_feedback,
)

# ---------------------------------------------------------------------------
# _hash_chunk
# ---------------------------------------------------------------------------


class TestHashChunk:
    def test_deterministic(self):
        h1 = _hash_chunk("some content")
        h2 = _hash_chunk("some content")
        assert h1 == h2

    def test_different_content_different_hash(self):
        h1 = _hash_chunk("content A")
        h2 = _hash_chunk("content B")
        assert h1 != h2

    def test_strips_whitespace(self):
        h1 = _hash_chunk("  content  ")
        h2 = _hash_chunk("content")
        assert h1 == h2

    def test_returns_16_chars(self):
        h = _hash_chunk("test")
        assert len(h) == 16


# ---------------------------------------------------------------------------
# _parse_rag_chunks
# ---------------------------------------------------------------------------


class TestParseRagChunks:
    def test_parses_standard_format(self):
        rag_text = (
            "--- Source 1 (m3ter_docs, relevance: 0.85) ---\n"
            "First chunk content here.\n\n"
            "--- Source 2 (user_docs, relevance: 0.72) ---\n"
            "Second chunk content here."
        )
        chunks = _parse_rag_chunks(rag_text)
        assert len(chunks) == 2
        assert chunks[0]["score"] == 0.85
        assert "First chunk content" in chunks[0]["content"]
        assert chunks[1]["score"] == 0.72
        assert "Second chunk content" in chunks[1]["content"]
        assert len(chunks[0]["hash"]) == 16

    def test_empty_input(self):
        assert _parse_rag_chunks("") == []

    def test_no_headers(self):
        assert _parse_rag_chunks("Just some random text without headers") == []

    def test_single_chunk(self):
        rag_text = "--- Source 1 (docs, relevance: 0.90) ---\nSingle chunk."
        chunks = _parse_rag_chunks(rag_text)
        assert len(chunks) == 1
        assert chunks[0]["score"] == 0.90


# ---------------------------------------------------------------------------
# _compute_approval_signal
# ---------------------------------------------------------------------------


class TestComputeApprovalSignal:
    def test_all_approved(self):
        decisions = [{"action": "approve"}, {"action": "approve"}]
        assert _compute_approval_signal(decisions) == 1.0

    def test_all_rejected(self):
        decisions = [{"action": "reject"}, {"action": "reject"}]
        assert _compute_approval_signal(decisions) == 0.0

    def test_mixed(self):
        decisions = [
            {"action": "approve"},
            {"action": "edit"},
            {"action": "reject"},
        ]
        signal = _compute_approval_signal(decisions)
        assert abs(signal - 0.5) < 0.01  # (1.0 + 0.5 + 0.0) / 3 = 0.5

    def test_empty_decisions(self):
        assert _compute_approval_signal([]) == 0.5

    def test_all_edits(self):
        decisions = [{"action": "edit"}, {"action": "edit"}]
        assert _compute_approval_signal(decisions) == 0.5


# ---------------------------------------------------------------------------
# record_rag_feedback + retrieve
# ---------------------------------------------------------------------------


class TestRecordAndRetrieveRagFeedback:
    @pytest.mark.asyncio
    async def test_record_and_retrieve(self):
        store = InMemoryStore()
        rag_context = (
            "--- Source 1 (docs, relevance: 0.85) ---\n"
            "Chunk A content.\n\n"
            "--- Source 2 (docs, relevance: 0.70) ---\n"
            "Chunk B content."
        )
        decisions = [{"action": "approve"}, {"action": "approve"}]

        await record_rag_feedback(store, "proj-1", "product", rag_context, decisions)

        feedback = await retrieve_rag_feedback(store, "proj-1")
        assert len(feedback) == 2
        # All approved → signal = 1.0 for first record
        for score in feedback.values():
            assert score == 1.0

    @pytest.mark.asyncio
    async def test_ema_update(self):
        store = InMemoryStore()
        rag_context = "--- Source 1 (docs, relevance: 0.85) ---\nChunk content."

        # First: all approved (signal=1.0)
        await record_rag_feedback(
            store,
            "proj-1",
            "product",
            rag_context,
            [{"action": "approve"}],
        )

        # Second: all rejected (signal=0.0)
        await record_rag_feedback(
            store,
            "proj-1",
            "product",
            rag_context,
            [{"action": "reject"}],
        )

        feedback = await retrieve_rag_feedback(store, "proj-1")
        assert len(feedback) == 1
        chunk_hash = list(feedback.keys())[0]
        # EMA: 0.3 * 0.0 + 0.7 * 1.0 = 0.7
        assert abs(feedback[chunk_hash] - 0.7) < 0.01

    @pytest.mark.asyncio
    async def test_empty_rag_context(self):
        store = InMemoryStore()
        await record_rag_feedback(store, "proj-1", "product", "", [])
        feedback = await retrieve_rag_feedback(store, "proj-1")
        assert feedback == {}

    @pytest.mark.asyncio
    async def test_empty_project(self):
        store = InMemoryStore()
        feedback = await retrieve_rag_feedback(store, "proj-nonexistent")
        assert feedback == {}


# ---------------------------------------------------------------------------
# rerank_with_feedback
# ---------------------------------------------------------------------------


@dataclass
class MockChunk:
    content: str
    metadata: dict
    score: float
    source_type: str


class TestRerankWithFeedback:
    def test_reranking_order(self):
        chunks = [
            MockChunk(
                content="low relevance high feedback",
                metadata={},
                score=0.5,
                source_type="m3ter",
            ),
            MockChunk(
                content="high relevance low feedback",
                metadata={},
                score=0.9,
                source_type="m3ter",
            ),
        ]
        # Give "low relevance" chunk high feedback score
        low_hash = _hash_chunk("low relevance high feedback")
        feedback = {low_hash: 1.0}

        # Without feedback: chunk 2 wins (0.9 > 0.5)
        # With feedback: chunk 1 = 0.7*0.5 + 0.3*1.0 = 0.65
        #                chunk 2 = 0.7*0.9 + 0.3*0.5 = 0.78
        # So chunk 2 should still win (relevance dominates at 0.7 weight)
        result = rerank_with_feedback(chunks, feedback)
        assert result[0].content == "high relevance low feedback"

    def test_feedback_can_change_order(self):
        chunks = [
            MockChunk(content="chunk a", metadata={}, score=0.6, source_type="m3ter"),
            MockChunk(content="chunk b", metadata={}, score=0.65, source_type="m3ter"),
        ]
        # Very low feedback for chunk b, high for chunk a
        a_hash = _hash_chunk("chunk a")
        b_hash = _hash_chunk("chunk b")
        feedback = {a_hash: 1.0, b_hash: 0.0}

        # chunk a: 0.7*0.6 + 0.3*1.0 = 0.72
        # chunk b: 0.7*0.65 + 0.3*0.0 = 0.455
        result = rerank_with_feedback(chunks, feedback)
        assert result[0].content == "chunk a"

    def test_missing_feedback_uses_neutral(self):
        chunks = [
            MockChunk(content="chunk x", metadata={}, score=0.8, source_type="m3ter"),
        ]
        # No feedback entry → uses 0.5 default
        result = rerank_with_feedback(chunks, {})
        assert len(result) == 1
        # Score: 0.7*0.8 + 0.3*0.5 = 0.71

    def test_empty_chunks(self):
        result = rerank_with_feedback([], {})
        assert result == []
