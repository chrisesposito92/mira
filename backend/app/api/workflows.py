"""API routes for workflows (read-only in Phase 4)."""

from uuid import UUID

from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.workflows import WorkflowResponse
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
):
    return svc.list_workflows(supabase, user_id, use_case_id)


@router.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return svc.get_workflow(supabase, user_id, workflow_id)
