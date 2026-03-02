"""Document text extraction and embedding pipeline."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

import asyncpg
from supabase import Client

from app.rag.ingestion import ingest_document

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(file_path: Path) -> str:
    """Extract text from a DOCX file using python-docx."""
    from docx import Document

    doc = Document(file_path)
    return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())


def extract_text_from_txt(file_path: Path) -> str:
    """Extract text from a plain text file."""
    return file_path.read_text(encoding="utf-8")


EXTRACTORS = {
    "pdf": extract_text_from_pdf,
    "docx": extract_text_from_docx,
    "txt": extract_text_from_txt,
    "csv": extract_text_from_txt,  # CSV treated as plain text
}


async def process_document(
    pool: asyncpg.Pool,
    supabase: Client,
    document_id: UUID,
    file_path: Path,
    file_type: str,
    project_id: UUID,
    on_progress: Callable[[str, str | None], Any] | None = None,
) -> int:
    """Extract text, chunk, embed, and store in pgvector.

    Updates document status in Supabase throughout the process.
    Returns the number of chunks created.

    When ``on_progress`` is provided, it is called at each stage with
    ``(stage, detail)`` so callers can stream real-time updates.
    The stages are: "chunking", "embedding", "storing".
    """
    # Update status to processing
    supabase.table("documents").update({"processing_status": "processing"}).eq(
        "id", str(document_id)
    ).execute()

    try:
        extractor = EXTRACTORS.get(file_type)
        if not extractor:
            raise ValueError(f"Unsupported file type: {file_type}")

        text = extractor(file_path)
        if not text.strip():
            raise ValueError("No text content extracted from document")

        metadata = {"filename": file_path.name, "file_type": file_type}

        chunk_count = await ingest_document(
            pool,
            content=text,
            source_type="user_document",
            metadata=metadata,
            project_id=project_id,
            source_id=document_id,
            on_progress=on_progress,
        )

        # Update status to ready with chunk count
        supabase.table("documents").update(
            {"processing_status": "ready", "chunk_count": chunk_count}
        ).eq("id", str(document_id)).execute()

        logger.info("Processed document %s: %d chunks", document_id, chunk_count)
        return chunk_count

    except Exception as e:
        logger.error("Failed to process document %s: %s", document_id, e)
        supabase.table("documents").update(
            {"processing_status": "failed", "error_message": str(e)}
        ).eq("id", str(document_id)).execute()
        raise
