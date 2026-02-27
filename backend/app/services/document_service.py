"""Service layer for documents CRUD."""

from uuid import UUID

from fastapi import HTTPException, UploadFile
from supabase import Client

from app.services.project_service import get_project

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

    row = {
        "project_id": str(project_id),
        "filename": file.filename,
        "file_type": ext,
        "file_size": len(content),
        "status": "pending",
    }
    result = supabase.table("documents").insert(row).execute()
    return result.data[0]


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


def delete_document(supabase: Client, user_id: UUID, document_id: UUID) -> None:
    get_document(supabase, user_id, document_id)
    supabase.table("documents").delete().eq("id", str(document_id)).execute()
