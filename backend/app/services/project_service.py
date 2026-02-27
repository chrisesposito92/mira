"""Service layer for projects CRUD."""

from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from app.schemas.projects import ProjectCreate, ProjectUpdate


def create_project(supabase: Client, user_id: UUID, data: ProjectCreate) -> dict:
    # Validate org_connection ownership if provided
    if data.org_connection_id:
        oc_result = (
            supabase.table("org_connections")
            .select("id")
            .eq("id", str(data.org_connection_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        if not oc_result.data:
            raise HTTPException(status_code=400, detail="Org connection not found or not owned")

    row = {
        "user_id": str(user_id),
        **data.model_dump(exclude_unset=True),
    }
    # Convert UUID fields to strings for Supabase
    if "org_connection_id" in row and row["org_connection_id"] is not None:
        row["org_connection_id"] = str(row["org_connection_id"])

    result = supabase.table("projects").insert(row).execute()
    return result.data[0]


def list_projects(supabase: Client, user_id: UUID) -> list[dict]:
    result = (
        supabase.table("projects")
        .select("*")
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_project(supabase: Client, user_id: UUID, project_id: UUID) -> dict:
    result = (
        supabase.table("projects")
        .select("*")
        .eq("id", str(project_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return result.data[0]


def update_project(
    supabase: Client, user_id: UUID, project_id: UUID, data: ProjectUpdate
) -> dict:
    get_project(supabase, user_id, project_id)

    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return get_project(supabase, user_id, project_id)

    if "org_connection_id" in updates and updates["org_connection_id"] is not None:
        oc_result = (
            supabase.table("org_connections")
            .select("id")
            .eq("id", str(updates["org_connection_id"]))
            .eq("user_id", str(user_id))
            .execute()
        )
        if not oc_result.data:
            raise HTTPException(status_code=400, detail="Org connection not found or not owned")
        updates["org_connection_id"] = str(updates["org_connection_id"])

    result = (
        supabase.table("projects")
        .update(updates)
        .eq("id", str(project_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    return result.data[0]


def delete_project(supabase: Client, user_id: UUID, project_id: UUID) -> None:
    get_project(supabase, user_id, project_id)
    supabase.table("projects").delete().eq("id", str(project_id)).eq(
        "user_id", str(user_id)
    ).execute()
