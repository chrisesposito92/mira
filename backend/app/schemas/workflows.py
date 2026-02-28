"""Schemas for workflows endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import WorkflowStatus, WorkflowType


class WorkflowResponse(BaseModel):
    id: UUID
    use_case_id: UUID
    workflow_type: WorkflowType
    status: WorkflowStatus
    thread_id: str | None = None
    model_id: str | None = None
    interrupt_payload: dict | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowStart(BaseModel):
    model_id: str = Field(..., description="LLM model ID from supported list")


class EntityDecision(BaseModel):
    index: int
    action: Literal["approve", "reject", "edit"]
    data: dict | None = None  # only for "edit" action


class WorkflowResume(BaseModel):
    decisions: list[EntityDecision]


class ClarificationAnswer(BaseModel):
    question_index: int
    selected_option: int | None = None
    free_text: str | None = None


class WorkflowResumeWithClarifications(BaseModel):
    answers: list[ClarificationAnswer]
