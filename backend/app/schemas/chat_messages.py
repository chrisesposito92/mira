"""Schemas for chat message endpoints."""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import MessageRole


class ChatMessageCreate(BaseModel):
    role: MessageRole
    content: str
    metadata: dict | None = None


class ChatMessageResponse(BaseModel):
    id: str
    workflow_id: str
    role: MessageRole
    content: str
    metadata: dict | None = None
    created_at: datetime
