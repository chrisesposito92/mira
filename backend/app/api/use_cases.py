"""API routes for use_cases."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.use_cases import UseCaseCreate, UseCaseResponse, UseCaseUpdate
from app.services import use_case_service as svc

router = APIRouter(tags=["use-cases"])


@router.post(
    "/api/projects/{project_id}/use-cases",
    response_model=UseCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_use_case(
    project_id: UUID,
    data: UseCaseCreate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return svc.create_use_case(supabase, user_id, project_id, data)


@router.get("/api/projects/{project_id}/use-cases", response_model=list[UseCaseResponse])
async def list_use_cases(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return svc.list_use_cases(supabase, user_id, project_id)


@router.get("/api/use-cases/{use_case_id}", response_model=UseCaseResponse)
async def get_use_case(
    use_case_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return svc.get_use_case(supabase, user_id, use_case_id)


@router.patch("/api/use-cases/{use_case_id}", response_model=UseCaseResponse)
async def update_use_case(
    use_case_id: UUID,
    data: UseCaseUpdate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return svc.update_use_case(supabase, user_id, use_case_id, data)


@router.delete("/api/use-cases/{use_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_use_case(
    use_case_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    svc.delete_use_case(supabase, user_id, use_case_id)
