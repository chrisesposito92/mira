"""API routes for workflows — read operations + LangGraph start/resume."""

from uuid import UUID

from fastapi import APIRouter, Depends
from supabase import Client

from app.agents.llm_factory import list_models
from app.dependencies import get_current_user, get_supabase
from app.schemas.workflows import (
    WorkflowResponse,
    WorkflowResume,
    WorkflowResumeWithClarifications,
    WorkflowStart,
)
from app.services import workflow_service as svc

router = APIRouter(tags=["workflows"])


@router.get(
    "/api/use-cases/{use_case_id}/workflows",
    response_model=list[WorkflowResponse],
)
async def list_workflows(
    use_case_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[dict]:
    return svc.list_workflows(supabase, user_id, use_case_id)


@router.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.get_workflow(supabase, user_id, workflow_id)


@router.post(
    "/api/use-cases/{use_case_id}/workflows/start",
    response_model=WorkflowResponse,
)
async def start_workflow(
    use_case_id: UUID,
    body: WorkflowStart,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """Start a new workflow for a use case."""
    return await svc.start_workflow(
        supabase, user_id, use_case_id, body.model_id, body.workflow_type
    )


@router.post(
    "/api/workflows/{workflow_id}/resume",
    response_model=WorkflowResponse,
)
async def resume_workflow(
    workflow_id: UUID,
    body: WorkflowResume,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """Resume a workflow with entity approval/reject/edit decisions."""
    decisions = [d.model_dump() for d in body.decisions]
    return await svc.resume_workflow(supabase, user_id, workflow_id, decisions)


@router.post(
    "/api/workflows/{workflow_id}/resume/clarification",
    response_model=WorkflowResponse,
)
async def resume_workflow_clarification(
    workflow_id: UUID,
    body: WorkflowResumeWithClarifications,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """Resume a workflow with clarification answers."""
    answers = [a.model_dump() for a in body.answers]
    return await svc.resume_workflow_clarification(supabase, user_id, workflow_id, answers)


@router.get("/api/models")
async def get_available_models() -> list[dict]:
    """List available LLM models for workflow execution."""
    return list_models()
