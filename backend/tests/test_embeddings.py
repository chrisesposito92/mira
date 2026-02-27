"""Tests for RAG embedding generation."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.embeddings import embed_single, embed_texts


def _mock_embedding_response(texts: list[str]) -> MagicMock:
    """Create a mock OpenAI embedding response."""
    response = MagicMock()
    response.data = []
    for i, _text in enumerate(texts):
        item = MagicMock()
        item.embedding = [0.1] * 1536
        response.data.append(item)
    return response


class TestEmbedTexts:
    async def test_returns_correct_dimensions(self):
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=_mock_embedding_response(["test"]))
        with patch("app.rag.embeddings.openai.AsyncOpenAI", return_value=mock_client):
            results = await embed_texts(["hello world"])
        assert len(results) == 1
        assert len(results[0]) == 1536

    async def test_empty_input_returns_empty(self):
        results = await embed_texts([])
        assert results == []

    async def test_batch_splitting(self):
        """Verify that >100 texts are split into multiple API calls."""
        mock_client = AsyncMock()
        call_count = 0

        async def mock_create(input, model):
            nonlocal call_count
            call_count += 1
            return _mock_embedding_response(input)

        mock_client.embeddings.create = mock_create
        with patch("app.rag.embeddings.openai.AsyncOpenAI", return_value=mock_client):
            texts = [f"text {i}" for i in range(150)]
            results = await embed_texts(texts, batch_size=100)
        assert len(results) == 150
        assert call_count == 2  # 100 + 50

    async def test_multiple_texts(self):
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(
            return_value=_mock_embedding_response(["a", "b", "c"])
        )
        with patch("app.rag.embeddings.openai.AsyncOpenAI", return_value=mock_client):
            results = await embed_texts(["a", "b", "c"])
        assert len(results) == 3


class TestEmbedSingle:
    async def test_returns_single_vector(self):
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=_mock_embedding_response(["test"]))
        with patch("app.rag.embeddings.openai.AsyncOpenAI", return_value=mock_client):
            result = await embed_single("hello")
        assert len(result) == 1536
        assert isinstance(result, list)
