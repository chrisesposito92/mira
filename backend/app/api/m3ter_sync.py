"""API endpoints for m3ter push/sync operations."""

from uuid import UUID

from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.m3ter_sync import (
    BulkPushRequest,
    BulkPushResultResponse,
    PushResultResponse,
    PushStatusResponse,
)
from app.services import push_service

router = APIRouter(tags=["m3ter-sync"])


@router.get(
    "/api/use-cases/{use_case_id}/push/status",
    response_model=PushStatusResponse,
)
async def get_push_status(
    use_case_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """Get push readiness info for a use case."""
    return push_service.get_push_status(supabase, user_id, use_case_id)


@router.post(
    "/api/objects/{object_id}/push",
    response_model=PushResultResponse,
)
async def push_single_object(
    object_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> PushResultResponse:
    """Push a single object to m3ter synchronously."""
    result = await push_service.push_object(supabase, user_id, object_id)
    return PushResultResponse(
        entity_id=result.entity_id,
        entity_type=result.entity_type,
        success=result.success,
        m3ter_id=result.m3ter_id,
        error=result.error,
    )


@router.post(
    "/api/use-cases/{use_case_id}/push",
    response_model=BulkPushResultResponse,
)
async def push_use_case_objects(
    use_case_id: UUID,
    body: BulkPushRequest | None = None,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> BulkPushResultResponse:
    """Push eligible objects for a use case to m3ter synchronously."""
    object_ids = body.object_ids if body else None
    result = await push_service.push_use_case_objects(supabase, user_id, use_case_id, object_ids)
    return BulkPushResultResponse(
        results=[
            PushResultResponse(
                entity_id=r.entity_id,
                entity_type=r.entity_type,
                success=r.success,
                m3ter_id=r.m3ter_id,
                error=r.error,
            )
            for r in result.results
        ],
        total=result.total,
        succeeded=result.succeeded,
        failed=result.failed,
        skipped=result.skipped,
    )
