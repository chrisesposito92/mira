"""API routes for projects."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import project_service as svc

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.create_project(supabase, user_id, data)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[dict]:
    return svc.list_projects(supabase, user_id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.get_project(supabase, user_id, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.update_project(supabase, user_id, project_id, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> None:
    svc.delete_project(supabase, user_id, project_id)
