"""API routes for component library."""

from uuid import UUID

from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.component_library import ComponentLibraryResponse
from app.services import component_library_service as svc

router = APIRouter(prefix="/api/component-library", tags=["component-library"])


@router.get("", response_model=list[ComponentLibraryResponse])
async def list_components(
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[dict]:
    return svc.list_components(supabase)


@router.get("/{component_id}", response_model=ComponentLibraryResponse)
async def get_component(
    component_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.get_component(supabase, component_id)
