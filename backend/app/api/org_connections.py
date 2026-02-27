"""API routes for org_connections."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.org_connections import (
    OrgConnectionCreate,
    OrgConnectionResponse,
    OrgConnectionTestResult,
    OrgConnectionUpdate,
)
from app.services import org_connection_service as svc

router = APIRouter(prefix="/api/org-connections", tags=["org-connections"])


@router.post("", response_model=OrgConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_org_connection(
    data: OrgConnectionCreate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return await svc.create_org_connection(supabase, user_id, data)


@router.get("", response_model=list[OrgConnectionResponse])
async def list_org_connections(
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[dict]:
    return svc.list_org_connections(supabase, user_id)


@router.get("/{connection_id}", response_model=OrgConnectionResponse)
async def get_org_connection(
    connection_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.get_org_connection(supabase, user_id, connection_id)


@router.patch("/{connection_id}", response_model=OrgConnectionResponse)
async def update_org_connection(
    connection_id: UUID,
    data: OrgConnectionUpdate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.update_org_connection(supabase, user_id, connection_id, data)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_org_connection(
    connection_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> None:
    svc.delete_org_connection(supabase, user_id, connection_id)


@router.post("/{connection_id}/test", response_model=OrgConnectionTestResult)
async def test_org_connection(
    connection_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return await svc.test_org_connection(supabase, user_id, connection_id)
