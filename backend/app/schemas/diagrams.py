"""Schemas for diagram endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DiagramSystem(BaseModel):
    """A system node placed on the diagram."""

    id: str  # Client-generated UUID string
    component_library_id: str | None = None
    name: str
    logo_base64: str | None = None
    x: float = 0.0
    y: float = 0.0
    category: str | None = None
    role: Literal["prospect", "hub", "system"] | None = None


class DiagramConnection(BaseModel):
    """A connection between two systems."""

    id: str  # Client-generated UUID string
    source_id: str
    target_id: str
    label: str = ""
    direction: Literal["unidirectional", "bidirectional"] = "unidirectional"
    connection_type: Literal["native_connector", "webhook_api", "custom_build", "api"] = "api"


class DiagramSettings(BaseModel):
    """Global diagram settings."""

    background_color: str = "#1a1f36"  # m3ter navy
    show_labels: bool = True


class DiagramContent(BaseModel):
    """Root content model stored as JSONB."""

    systems: list[DiagramSystem] = Field(default_factory=list)
    connections: list[DiagramConnection] = Field(default_factory=list)
    settings: DiagramSettings = Field(default_factory=DiagramSettings)


class DiagramCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    title: str = ""
    project_id: UUID | None = None
    content: DiagramContent = Field(default_factory=DiagramContent)


class DiagramUpdate(BaseModel):
    """Partial update model for PATCH endpoint.

    All fields optional -- only provided fields are updated.
    Addresses review concern: missing PATCH/update endpoint.
    """

    customer_name: str | None = Field(None, min_length=1, max_length=255)
    title: str | None = None
    project_id: UUID | None = None
    content: DiagramContent | None = None
    thumbnail_base64: str | None = None


class DiagramResponse(BaseModel):
    """Full diagram response including content -- used for GET /{id}."""

    id: UUID
    user_id: UUID
    customer_name: str
    title: str
    project_id: UUID | None = None
    content: DiagramContent
    schema_version: int
    thumbnail_base64: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DiagramListResponse(BaseModel):
    """Lightweight diagram response for list endpoint.

    Excludes content and thumbnail_base64 to avoid returning large
    JSONB payloads and base64 strings in list queries.
    Addresses review concern: list performance degradation.
    """

    id: UUID
    user_id: UUID
    customer_name: str
    title: str
    project_id: UUID | None = None
    schema_version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
