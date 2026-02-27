"""Service layer for generated_objects CRUD."""

from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from app.schemas.generated_objects import GeneratedObjectUpdate


def list_objects(
    supabase: Client,
    user_id: UUID,
    use_case_id: UUID,
    entity_type: str | None = None,
    status: str | None = None,
) -> list[dict]:
    # Verify ownership through use_case → project chain
    _verify_use_case_ownership(supabase, user_id, use_case_id)

    query = (
        supabase.table("generated_objects")
        .select("*")
        .eq("use_case_id", str(use_case_id))
    )
    if entity_type:
        query = query.eq("entity_type", entity_type)
    if status:
        query = query.eq("status", status)

    result = query.order("created_at", desc=True).execute()
    return result.data


def get_object(supabase: Client, user_id: UUID, object_id: UUID) -> dict:
    result = (
        supabase.table("generated_objects")
        .select("*, use_cases!inner(project_id, projects!inner(user_id))")
        .eq("id", str(object_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Generated object not found")
    row = result.data[0]
    project_user_id = row.get("use_cases", {}).get("projects", {}).get("user_id")
    if project_user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Generated object not found")
    return {k: v for k, v in row.items() if k != "use_cases"}


def update_object(
    supabase: Client, user_id: UUID, object_id: UUID, data: GeneratedObjectUpdate
) -> dict:
    get_object(supabase, user_id, object_id)

    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return get_object(supabase, user_id, object_id)

    result = (
        supabase.table("generated_objects")
        .update(updates)
        .eq("id", str(object_id))
        .execute()
    )
    return result.data[0]


def bulk_update_status(
    supabase: Client, user_id: UUID, ids: list[UUID], status: str
) -> list[dict]:
    # Verify ownership of each object
    for obj_id in ids:
        get_object(supabase, user_id, obj_id)

    str_ids = [str(i) for i in ids]
    result = (
        supabase.table("generated_objects")
        .update({"status": status})
        .in_("id", str_ids)
        .execute()
    )
    return result.data


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
