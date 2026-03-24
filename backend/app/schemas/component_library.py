"""Schemas for component library endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ComponentLibraryResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    domain: str
    category: str
    logo_base64: str | None = None
    is_native_connector: bool
    display_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
