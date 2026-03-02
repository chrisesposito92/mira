"""Service layer for documents CRUD."""

import asyncio
import logging
from pathlib import Path, PurePosixPath
from uuid import UUID

from fastapi import HTTPException, UploadFile
from supabase import Client

from app.config import settings
from app.db.client import get_db_pool
from app.rag.ingestion import delete_by_source_id
from app.services.document_processing_registry import notify_listeners
from app.services.document_processor import process_document
from app.services.project_service import get_project

logger = logging.getLogger(__name__)

ALLOWED_FILE_TYPES = {"pdf", "docx", "txt", "csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def upload_document(
    supabase: Client, user_id: UUID, project_id: UUID, file: UploadFile
) -> dict:
    get_project(supabase, user_id, project_id)

    # Validate file type
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: "
            f"{', '.join(sorted(ALLOWED_FILE_TYPES))}",
        )

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10 MB limit")

    safe_filename = PurePosixPath(file.filename or "upload").name

    # Insert DB row first to get a unique document ID
    row = {
        "project_id": str(project_id),
        "filename": safe_filename,
        "file_type": ext,
        "file_size_bytes": len(content),
        "storage_path": "pending",
        "processing_status": "pending",
    }
    result = supabase.table("documents").insert(row).execute()
    doc = result.data[0]
    doc_id = doc["id"]

    # Save file to disk using document UUID for uniqueness
    try:
        upload_path = Path(settings.upload_dir) / str(project_id)
        upload_path.mkdir(parents=True, exist_ok=True)
        file_path = upload_path / f"{doc_id}_{safe_filename}"
        file_path.write_bytes(content)
    except OSError:
        # File write failed — clean up the orphaned DB row
        logger.exception("File write failed for document %s", doc_id)
        supabase.table("documents").delete().eq("id", doc_id).execute()
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Update storage_path now that file is written
    supabase.table("documents").update({"storage_path": str(file_path)}).eq("id", doc_id).execute()

    # Fire-and-forget: process document in background, stream progress via WebSocket
    pid = str(project_id)
    did = doc_id

    async def _process_and_notify() -> None:
        try:
            await notify_listeners(
                pid,
                {
                    "type": "doc_processing_started",
                    "document_id": did,
                    "filename": safe_filename,
                    "stage": "extracting",
                },
            )

            async def _on_progress(stage: str, detail: str | None) -> None:
                msg: dict = {
                    "type": "doc_processing_progress",
                    "document_id": did,
                    "stage": stage,
                }
                if detail is not None:
                    msg["detail"] = detail
                await notify_listeners(pid, msg)

            pool = await get_db_pool()
            chunk_count = await process_document(
                pool=pool,
                supabase=supabase,
                document_id=UUID(did),
                file_path=file_path,
                file_type=ext,
                project_id=project_id,
                on_progress=_on_progress,
            )

            await notify_listeners(
                pid,
                {
                    "type": "doc_processing_complete",
                    "document_id": did,
                    "chunk_count": chunk_count,
                },
            )
        except Exception as exc:
            logger.exception("Document processing failed for %s", did)
            # Ensure status reflects the failure (process_document already sets it,
            # but guard against errors before that point)
            try:
                supabase.table("documents").update(
                    {"processing_status": "failed", "error_message": str(exc)}
                ).eq("id", did).execute()
            except Exception:
                logger.exception("Failed to update error status for document %s", did)

            await notify_listeners(
                pid,
                {
                    "type": "doc_processing_error",
                    "document_id": did,
                    "error": str(exc),
                },
            )

    asyncio.create_task(_process_and_notify())

    # Return immediately with pending status
    return doc


def list_documents(supabase: Client, user_id: UUID, project_id: UUID) -> list[dict]:
    get_project(supabase, user_id, project_id)
    result = (
        supabase.table("documents")
        .select("*")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_document(supabase: Client, user_id: UUID, document_id: UUID) -> dict:
    result = (
        supabase.table("documents")
        .select("*, projects!inner(user_id)")
        .eq("id", str(document_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    row = result.data[0]
    if row.get("projects", {}).get("user_id") != str(user_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {k: v for k, v in row.items() if k != "projects"}


async def delete_document(supabase: Client, user_id: UUID, document_id: UUID) -> None:
    existing = get_document(supabase, user_id, document_id)

    # Clean up embeddings
    pool = await get_db_pool()
    await delete_by_source_id(pool, document_id)

    # Clean up file from disk
    storage_path = existing.get("storage_path", "")
    if storage_path:
        Path(storage_path).unlink(missing_ok=True)

    supabase.table("documents").delete().eq("id", str(document_id)).eq(
        "project_id", existing["project_id"]
    ).execute()
