"""Schemas for projects endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    customer_name: str | None = None
    description: str | None = None
    org_connection_id: UUID | None = None
    default_model_id: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    customer_name: str | None = None
    description: str | None = None
    org_connection_id: UUID | None = None
    default_model_id: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    customer_name: str | None = None
    description: str | None = None
    org_connection_id: UUID | None = None
    default_model_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
