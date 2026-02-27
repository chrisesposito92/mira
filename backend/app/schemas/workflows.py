"""Schemas for workflows endpoints (read-only in Phase 4)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import WorkflowStatus, WorkflowType


class WorkflowResponse(BaseModel):
    id: UUID
    use_case_id: UUID
    workflow_type: WorkflowType
    status: WorkflowStatus
    thread_id: str | None = None
    interrupt_payload: dict | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
