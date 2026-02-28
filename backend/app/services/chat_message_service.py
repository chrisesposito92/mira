"""Service layer for chat message persistence."""

import logging
from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from app.schemas.chat_messages import ChatMessageCreate

logger = logging.getLogger(__name__)


def _verify_workflow_ownership(supabase: Client, user_id: UUID, workflow_id: str) -> None:
    """Verify the user owns the workflow via use_cases -> projects join."""
    result = (
        supabase.table("workflows")
        .select("id, use_cases!inner(id, projects!inner(user_id))")
        .eq("id", workflow_id)
        .eq("use_cases.projects.user_id", str(user_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Workflow not found")


def list_messages(
    supabase: Client, user_id: UUID, workflow_id: str, limit: int = 100
) -> list[dict]:
    """List chat messages for a workflow, ordered by created_at ASC."""
    _verify_workflow_ownership(supabase, user_id, workflow_id)
    result = (
        supabase.table("chat_messages")
        .select("*")
        .eq("workflow_id", workflow_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data


def create_message(
    supabase: Client, user_id: UUID, workflow_id: str, data: ChatMessageCreate
) -> dict:
    """Create a chat message with ownership check."""
    _verify_workflow_ownership(supabase, user_id, workflow_id)
    row = {
        "workflow_id": workflow_id,
        "role": data.role,
        "content": data.content,
        "metadata": data.metadata or {},
    }
    result = supabase.table("chat_messages").insert(row).execute()
    return result.data[0]


def save_message_internal(
    supabase: Client,
    workflow_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> dict | None:
    """Save a chat message without auth check — for internal WS handler use only."""
    try:
        row = {
            "workflow_id": workflow_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }
        result = supabase.table("chat_messages").insert(row).execute()
        return result.data[0] if result.data else None
    except Exception:
        logger.exception("Failed to save chat message for workflow %s", workflow_id)
        return None
