"""RAG (Retrieval-Augmented Generation) pipeline."""

from app.rag.chunker import TextChunk, chunk_text
from app.rag.embeddings import embed_single, embed_texts
from app.rag.ingestion import (
    delete_by_source_id,
    delete_by_source_type,
    ingest_batch,
    ingest_document,
)
from app.rag.retriever import RetrievedChunk, retrieve

__all__ = [
    "RetrievedChunk",
    "TextChunk",
    "chunk_text",
    "delete_by_source_id",
    "delete_by_source_type",
    "embed_single",
    "embed_texts",
    "ingest_batch",
    "ingest_document",
    "retrieve",
]
