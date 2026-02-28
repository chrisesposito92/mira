"""API routes for chat messages — list and create."""

from uuid import UUID

from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.chat_messages import ChatMessageCreate, ChatMessageResponse
from app.services import chat_message_service as svc

router = APIRouter(prefix="/api/workflows", tags=["chat-messages"])


@router.get("/{workflow_id}/messages", response_model=list[ChatMessageResponse])
async def list_messages(
    workflow_id: str,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[dict]:
    return svc.list_messages(supabase, user_id, workflow_id)


@router.post(
    "/{workflow_id}/messages",
    response_model=ChatMessageResponse,
    status_code=201,
)
async def create_message(
    workflow_id: str,
    data: ChatMessageCreate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.create_message(supabase, user_id, workflow_id, data)
