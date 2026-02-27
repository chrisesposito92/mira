"""Tests for RAG two-source retriever."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.rag.retriever import RetrievedChunk, retrieve


def _make_mock_pool(fetch_results=None):
    """Create a mock asyncpg pool with configurable fetch results."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(side_effect=fetch_results or [[]])

    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=False)

    mock_pool = AsyncMock()
    mock_pool.acquire = MagicMock(return_value=mock_acquire)

    return mock_pool, mock_conn


def _mock_row(content, score, source_type, metadata=None):
    """Create a mock database row dict."""
    return {
        "content": content,
        "metadata": metadata or "{}",
        "score": score,
        "source_type": source_type,
    }


class TestRetrieve:
    async def test_m3ter_docs_only(self):
        """Without project_id, only m3ter_docs are queried."""
        rows = [_mock_row("doc content", 0.9, "m3ter_docs")]
        mock_pool, mock_conn = _make_mock_pool(fetch_results=[rows])

        with patch("app.rag.retriever.embed_single", AsyncMock(return_value=[0.1] * 1536)):
            results = await retrieve(mock_pool, "test query", k=5)

        assert len(results) == 1
        assert results[0].content == "doc content"
        assert results[0].source_type == "m3ter_docs"
        assert results[0].score == 0.9
        assert mock_conn.fetch.call_count == 1

    async def test_two_source_merge(self):
        """With project_id, both sources queried and merged by score descending."""
        m3ter_rows = [_mock_row("m3ter doc", 0.8, "m3ter_docs")]
        user_rows = [_mock_row("user doc", 0.95, "user_document")]
        mock_pool, mock_conn = _make_mock_pool(fetch_results=[m3ter_rows, user_rows])

        with patch("app.rag.retriever.embed_single", AsyncMock(return_value=[0.1] * 1536)):
            results = await retrieve(mock_pool, "test query", project_id=uuid4(), k=5)

        assert len(results) == 2
        assert results[0].source_type == "user_document"
        assert results[0].score == 0.95
        assert results[1].source_type == "m3ter_docs"
        assert results[1].score == 0.8
        assert mock_conn.fetch.call_count == 2

    async def test_empty_results(self):
        mock_pool, _ = _make_mock_pool(fetch_results=[[]])

        with patch("app.rag.retriever.embed_single", AsyncMock(return_value=[0.1] * 1536)):
            results = await retrieve(mock_pool, "test query", k=5)

        assert results == []

    async def test_k_limit_respected(self):
        """Results should be limited to k even with more candidates."""
        rows = [_mock_row(f"doc {i}", 0.9 - i * 0.05, "m3ter_docs") for i in range(10)]
        mock_pool, _ = _make_mock_pool(fetch_results=[rows])

        with patch("app.rag.retriever.embed_single", AsyncMock(return_value=[0.1] * 1536)):
            results = await retrieve(mock_pool, "test", k=3)

        assert len(results) == 3

    async def test_returns_retrieved_chunk_instances(self):
        rows = [_mock_row("content", 0.85, "m3ter_docs")]
        mock_pool, _ = _make_mock_pool(fetch_results=[rows])

        with patch("app.rag.retriever.embed_single", AsyncMock(return_value=[0.1] * 1536)):
            results = await retrieve(mock_pool, "test", k=5)

        assert all(isinstance(r, RetrievedChunk) for r in results)

    async def test_metadata_json_string_parsed(self):
        """JSON string metadata should be parsed to dict."""
        rows = [_mock_row("content", 0.9, "m3ter_docs", metadata='{"title": "Test"}')]
        mock_pool, _ = _make_mock_pool(fetch_results=[rows])

        with patch("app.rag.retriever.embed_single", AsyncMock(return_value=[0.1] * 1536)):
            results = await retrieve(mock_pool, "test", k=5)

        assert results[0].metadata == {"title": "Test"}

    async def test_metadata_dict_passthrough(self):
        """Dict metadata (already parsed by asyncpg) should pass through unchanged."""
        rows = [_mock_row("content", 0.9, "m3ter_docs", metadata={"key": "value"})]
        mock_pool, _ = _make_mock_pool(fetch_results=[rows])

        with patch("app.rag.retriever.embed_single", AsyncMock(return_value=[0.1] * 1536)):
            results = await retrieve(mock_pool, "test", k=5)

        assert results[0].metadata == {"key": "value"}

    async def test_score_ordering(self):
        """Results from a single source should be ordered by score descending."""
        rows = [
            _mock_row("low", 0.5, "m3ter_docs"),
            _mock_row("high", 0.95, "m3ter_docs"),
            _mock_row("mid", 0.75, "m3ter_docs"),
        ]
        mock_pool, _ = _make_mock_pool(fetch_results=[rows])

        with patch("app.rag.retriever.embed_single", AsyncMock(return_value=[0.1] * 1536)):
            results = await retrieve(mock_pool, "test", k=5)

        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)
