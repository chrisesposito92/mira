"""Service layer for workflows (read-only in Phase 4)."""

from uuid import UUID

from fastapi import HTTPException
from supabase import Client


def list_workflows(supabase: Client, user_id: UUID, use_case_id: UUID) -> list[dict]:
    _verify_use_case_ownership(supabase, user_id, use_case_id)
    result = (
        supabase.table("workflows")
        .select("*")
        .eq("use_case_id", str(use_case_id))
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_workflow(supabase: Client, user_id: UUID, workflow_id: UUID) -> dict:
    result = (
        supabase.table("workflows")
        .select("*, use_cases!inner(project_id, projects!inner(user_id))")
        .eq("id", str(workflow_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    row = result.data[0]
    project_user_id = row.get("use_cases", {}).get("projects", {}).get("user_id")
    if project_user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {k: v for k, v in row.items() if k != "use_cases"}


def _verify_use_case_ownership(supabase: Client, user_id: UUID, use_case_id: UUID) -> None:
    result = (
        supabase.table("use_cases")
        .select("id, projects!inner(user_id)")
        .eq("id", str(use_case_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Use case not found")
    if result.data[0].get("projects", {}).get("user_id") != str(user_id):
        raise HTTPException(status_code=404, detail="Use case not found")
