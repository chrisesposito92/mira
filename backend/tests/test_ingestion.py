"""Tests for RAG ingestion pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.rag.chunker import TextChunk
from app.rag.ingestion import (
    delete_by_source_id,
    delete_by_source_type,
    ingest_batch,
    ingest_document,
)


def _make_mock_pool(execute_return="DELETE 0"):
    """Create a mock asyncpg pool with nested async context managers."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=execute_return)

    # conn.transaction() returns an async context manager
    mock_tx = AsyncMock()
    mock_tx.__aenter__ = AsyncMock(return_value=mock_tx)
    mock_tx.__aexit__ = AsyncMock(return_value=False)
    mock_conn.transaction = MagicMock(return_value=mock_tx)

    # pool.acquire() returns an async context manager yielding conn
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=False)
    mock_pool = AsyncMock()
    mock_pool.acquire = MagicMock(return_value=mock_acquire)

    return mock_pool, mock_conn


class TestIngestDocument:
    async def test_chunks_and_stores(self):
        mock_pool, mock_conn = _make_mock_pool()
        mock_embeddings = [[0.1] * 1536, [0.2] * 1536]

        with (
            patch("app.rag.ingestion.embed_texts", AsyncMock(return_value=mock_embeddings)),
            patch(
                "app.rag.ingestion.chunk_text",
                return_value=[
                    TextChunk(
                        content="chunk 1",
                        metadata={"chunk_index": 0},
                        chunk_index=0,
                        total_chunks=2,
                    ),
                    TextChunk(
                        content="chunk 2",
                        metadata={"chunk_index": 1},
                        chunk_index=1,
                        total_chunks=2,
                    ),
                ],
            ),
        ):
            count = await ingest_document(mock_pool, "test content", "m3ter_docs")

        assert count == 2
        assert mock_conn.execute.call_count == 2

    async def test_empty_content_returns_zero(self):
        mock_pool, _ = _make_mock_pool()
        count = await ingest_document(mock_pool, "", "m3ter_docs")
        assert count == 0

    async def test_whitespace_only_returns_zero(self):
        mock_pool, _ = _make_mock_pool()
        count = await ingest_document(mock_pool, "   \n  ", "m3ter_docs")
        assert count == 0

    async def test_with_project_and_source_ids(self):
        mock_pool, mock_conn = _make_mock_pool()
        project_id = uuid4()
        source_id = uuid4()

        with (
            patch("app.rag.ingestion.embed_texts", AsyncMock(return_value=[[0.1] * 1536])),
            patch(
                "app.rag.ingestion.chunk_text",
                return_value=[
                    TextChunk(content="chunk", metadata={}, chunk_index=0, total_chunks=1),
                ],
            ),
        ):
            count = await ingest_document(
                mock_pool,
                "content",
                "user_document",
                project_id=project_id,
                source_id=source_id,
            )

        assert count == 1
        call_args = mock_conn.execute.call_args
        # Positional args: SQL, source_type, source_id, project_id, content, metadata, embedding
        assert call_args.args[1] == "user_document"
        assert call_args.args[2] == str(source_id)
        assert call_args.args[3] == str(project_id)

    async def test_none_ids_passed_as_none(self):
        mock_pool, mock_conn = _make_mock_pool()

        with (
            patch("app.rag.ingestion.embed_texts", AsyncMock(return_value=[[0.1] * 1536])),
            patch(
                "app.rag.ingestion.chunk_text",
                return_value=[
                    TextChunk(content="chunk", metadata={}, chunk_index=0, total_chunks=1),
                ],
            ),
        ):
            await ingest_document(mock_pool, "content", "m3ter_docs")

        call_args = mock_conn.execute.call_args
        assert call_args.args[2] is None  # source_id
        assert call_args.args[3] is None  # project_id


class TestIngestBatch:
    async def test_ingests_multiple_pages(self):
        pages = [
            {"content": "Page 1 content", "title": "Page 1", "url": "https://example.com/1"},
            {"content": "Page 2 content", "title": "Page 2", "url": "https://example.com/2"},
        ]
        with patch("app.rag.ingestion.ingest_document", AsyncMock(return_value=3)) as mock_ingest:
            total = await ingest_batch(AsyncMock(), pages, "m3ter_docs")

        assert total == 6
        assert mock_ingest.call_count == 2

    async def test_empty_pages_returns_zero(self):
        with patch("app.rag.ingestion.ingest_document", AsyncMock(return_value=0)):
            total = await ingest_batch(AsyncMock(), [], "m3ter_docs")
        assert total == 0

    async def test_passes_metadata_from_page(self):
        pages = [{"content": "text", "title": "My Title", "url": "https://example.com"}]
        with patch("app.rag.ingestion.ingest_document", AsyncMock(return_value=1)) as mock_ingest:
            await ingest_batch(AsyncMock(), pages, "m3ter_docs")

        call_kwargs = mock_ingest.call_args
        assert call_kwargs.kwargs["metadata"] == {
            "title": "My Title",
            "source_url": "https://example.com",
        }


class TestDeleteBySourceType:
    async def test_returns_delete_count(self):
        mock_pool, _ = _make_mock_pool(execute_return="DELETE 5")
        count = await delete_by_source_type(mock_pool, "m3ter_docs")
        assert count == 5

    async def test_zero_deletes(self):
        mock_pool, _ = _make_mock_pool(execute_return="DELETE 0")
        count = await delete_by_source_type(mock_pool, "m3ter_docs")
        assert count == 0


class TestDeleteBySourceId:
    async def test_returns_delete_count(self):
        mock_pool, _ = _make_mock_pool(execute_return="DELETE 3")
        count = await delete_by_source_id(mock_pool, uuid4())
        assert count == 3

    async def test_passes_string_source_id(self):
        mock_pool, mock_conn = _make_mock_pool(execute_return="DELETE 1")
        sid = uuid4()
        await delete_by_source_id(mock_pool, sid)
        call_args = mock_conn.execute.call_args
        assert call_args.args[1] == str(sid)
