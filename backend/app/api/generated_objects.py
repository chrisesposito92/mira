"""API routes for generated_objects."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.common import MessageResponse
from app.schemas.generated_objects import (
    BulkStatusUpdate,
    GeneratedObjectResponse,
    GeneratedObjectUpdate,
)
from app.services import generated_object_service as svc

router = APIRouter(tags=["generated-objects"])


@router.get(
    "/api/use-cases/{use_case_id}/objects",
    response_model=list[GeneratedObjectResponse],
)
async def list_objects(
    use_case_id: UUID,
    entity_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[dict]:
    return svc.list_objects(supabase, user_id, use_case_id, entity_type, status_filter)


@router.get("/api/objects/{object_id}", response_model=GeneratedObjectResponse)
async def get_object(
    object_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.get_object(supabase, user_id, object_id)


@router.patch("/api/objects/{object_id}", response_model=GeneratedObjectResponse)
async def update_object(
    object_id: UUID,
    data: GeneratedObjectUpdate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.update_object(supabase, user_id, object_id, data)


@router.post("/api/objects/bulk-status", response_model=MessageResponse)
async def bulk_update_status(
    data: BulkStatusUpdate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> MessageResponse:
    updated = svc.bulk_update_status(supabase, user_id, data.ids, data.status)
    return MessageResponse(message=f"Updated {len(updated)} objects to '{data.status}'")
