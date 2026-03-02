"""REST endpoint for use case generator file text extraction."""

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.use_case_generator import ExtractTextResponse
from app.services.document_processor import EXTRACTORS
from app.services.document_service import ALLOWED_FILE_TYPES, MAX_FILE_SIZE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["use-case-generator"])


@router.post(
    "/api/projects/{project_id}/generate-use-cases/extract-text",
    response_model=ExtractTextResponse,
)
async def extract_text(
    project_id: UUID,
    file: UploadFile,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> ExtractTextResponse:
    """Extract text from an uploaded file for use in use case generation.

    Validates file type and size, extracts text in-memory using existing
    EXTRACTORS, and returns the text content.
    """
    # Verify project ownership
    project_result = (
        supabase.table("projects").select("id, user_id").eq("id", str(project_id)).execute()
    )
    if not project_result.data or project_result.data[0].get("user_id") != str(user_id):
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate file
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_FILE_TYPES:
        allowed = ", ".join(sorted(ALLOWED_FILE_TYPES))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {allowed}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10 MB.")

    # Extract text using existing extractors
    extractor = EXTRACTORS.get(ext)
    if not extractor:
        raise HTTPException(status_code=400, detail=f"No extractor for file type: {ext}")

    try:
        # Write to temp file since extractors expect file paths
        with NamedTemporaryFile(suffix=f".{ext}", delete=True) as tmp:
            tmp.write(content)
            tmp.flush()
            text = extractor(Path(tmp.name))
    except Exception as exc:
        logger.exception("Text extraction failed for %s", filename)
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {exc}")

    if not text.strip():
        raise HTTPException(
            status_code=400, detail="No text content could be extracted from the file."
        )

    return ExtractTextResponse(text=text)
