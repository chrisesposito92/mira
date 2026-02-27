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
    file_size: int
    status: DocumentStatus
    chunk_count: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
