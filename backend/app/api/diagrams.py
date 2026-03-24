"""API routes for diagrams."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.diagrams import (
    DiagramCreate,
    DiagramListResponse,
    DiagramResponse,
    DiagramUpdate,
)
from app.services import diagram_service as svc

router = APIRouter(prefix="/api/diagrams", tags=["diagrams"])


@router.post("", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    data: DiagramCreate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.create_diagram(supabase, user_id, data)


@router.get("", response_model=list[DiagramListResponse])
async def list_diagrams(
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[dict]:
    return svc.list_diagrams(supabase, user_id)


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    diagram_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.get_diagram(supabase, user_id, diagram_id)


@router.patch("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    diagram_id: UUID,
    data: DiagramUpdate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """Partial update of a diagram. Addresses review concern: missing PATCH endpoint."""
    return svc.update_diagram(supabase, user_id, diagram_id, data)


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(
    diagram_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> None:
    svc.delete_diagram(supabase, user_id, diagram_id)
