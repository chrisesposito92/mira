"""Schemas for documents endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import DocumentStatus


class DocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    file_type: str
    storage_path: str
    processing_status: DocumentStatus
    chunk_count: int = 0
    file_size_bytes: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
