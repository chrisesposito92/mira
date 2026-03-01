"""Schemas for generated_objects endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import EntityType, ObjectStatus


class GeneratedObjectResponse(BaseModel):
    id: UUID
    use_case_id: UUID
    entity_type: EntityType
    name: str | None = None
    code: str | None = None
    status: ObjectStatus
    data: dict | None = None
    validation_errors: list[dict] | None = None
    m3ter_id: str | None = None
    depends_on: list[UUID] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeneratedObjectUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    status: ObjectStatus | None = None
    data: dict | None = None


class CreateGeneratedObject(BaseModel):
    entity_type: EntityType
    name: str | None = None
    code: str | None = None
    data: dict | None = None


class BulkStatusUpdate(BaseModel):
    ids: list[UUID]
    status: ObjectStatus
