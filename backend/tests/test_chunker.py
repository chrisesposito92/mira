"""Tests for RAG text chunker."""

from app.rag.chunker import TextChunk, chunk_text


class TestChunkText:
    def test_short_text_single_chunk(self):
        chunks = chunk_text("Hello, world!")
        assert len(chunks) == 1
        assert chunks[0].content == "Hello, world!"
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks == 1

    def test_empty_text_returns_empty(self):
        assert chunk_text("") == []

    def test_whitespace_only_returns_empty(self):
        assert chunk_text("   \n\n  ") == []

    def test_long_text_multiple_chunks(self):
        text = "word " * 2000  # ~10000 chars
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=100)
        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.total_chunks == len(chunks)

    def test_metadata_propagation(self):
        meta = {"source_url": "https://example.com", "title": "Test"}
        chunks = chunk_text("Hello, world!", metadata=meta)
        assert len(chunks) == 1
        assert chunks[0].metadata["source_url"] == "https://example.com"
        assert chunks[0].metadata["title"] == "Test"
        assert chunks[0].metadata["chunk_index"] == 0
        assert chunks[0].metadata["total_chunks"] == 1

    def test_chunk_overlap(self):
        text = "\n\n".join(f"Paragraph {i} with some content here." for i in range(100))
        chunks = chunk_text(text, chunk_size=200, chunk_overlap=50)
        assert len(chunks) > 2
        for i in range(len(chunks) - 1):
            tail = chunks[i].content[-50:]
            overlap_found = any(
                word in chunks[i + 1].content for word in tail.split() if len(word) > 3
            )
            assert overlap_found, f"No overlap found between chunks {i} and {i + 1}"

    def test_markdown_header_splitting(self):
        text = (
            "# Title\n\nIntro paragraph.\n\n## Section One\n\n"
            + "Content A. " * 500
            + "\n\n## Section Two\n\n"
            + "Content B. " * 500
        )
        chunks = chunk_text(text, chunk_size=2000, chunk_overlap=100)
        starts = [c.content.strip()[:20] for c in chunks]
        assert any("Section" in s for s in starts), (
            f"Expected markdown header split, got starts: {starts}"
        )

    def test_returns_text_chunk_instances(self):
        chunks = chunk_text("Test text")
        assert all(isinstance(c, TextChunk) for c in chunks)

    def test_default_metadata_when_none(self):
        chunks = chunk_text("Some text")
        assert chunks[0].metadata == {"chunk_index": 0, "total_chunks": 1}
