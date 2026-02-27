"""Text chunking for RAG pipeline."""

from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class TextChunk:
    content: str
    metadata: dict = field(default_factory=dict)
    chunk_index: int = 0
    total_chunks: int = 0


def chunk_text(
    text: str,
    metadata: dict | None = None,
    chunk_size: int = 4000,
    chunk_overlap: int = 200,
) -> list[TextChunk]:
    """Split text into overlapping chunks with metadata."""
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    splits = splitter.split_text(text)
    base_meta = metadata or {}
    return [
        TextChunk(
            content=chunk,
            metadata={**base_meta, "chunk_index": i, "total_chunks": len(splits)},
            chunk_index=i,
            total_chunks=len(splits),
        )
        for i, chunk in enumerate(splits)
    ]
