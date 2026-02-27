"""Schemas for org_connections endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ConnectionStatus


class OrgConnectionCreate(BaseModel):
    org_id: str = Field(..., min_length=1)
    org_name: str = Field(..., min_length=1)
    api_url: str = "https://api.m3ter.com"
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)


class OrgConnectionUpdate(BaseModel):
    org_name: str | None = None
    api_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None


class OrgConnectionResponse(BaseModel):
    id: UUID
    user_id: UUID
    org_id: str
    org_name: str
    api_url: str
    status: ConnectionStatus
    last_tested_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrgConnectionTestResult(BaseModel):
    success: bool
    message: str
    tested_at: datetime
