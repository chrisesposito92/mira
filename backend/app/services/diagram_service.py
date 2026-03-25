"""Service layer for diagrams CRUD."""

from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from app.schemas.diagrams import DiagramCreate, DiagramUpdate

# Fields to SELECT for list queries -- excludes content JSONB for performance
# but includes thumbnail_base64 for card display (typically 5-15KB)
LIST_SELECT_FIELDS = (
    "id,user_id,customer_name,title,project_id,schema_version,"
    "thumbnail_base64,created_at,updated_at"
)


def _verify_project_ownership(supabase: Client, user_id: UUID, project_id: UUID) -> None:
    """Verify project exists and belongs to the user before linking."""
    result = (
        supabase.table("projects")
        .select("id")
        .eq("id", str(project_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")


def create_diagram(supabase: Client, user_id: UUID, data: DiagramCreate) -> dict:
    row = {
        "user_id": str(user_id),
        **data.model_dump(exclude_unset=True, mode="json"),
    }
    row["schema_version"] = 1
    # Convert UUID fields to strings for Supabase
    if "project_id" in row and row["project_id"] is not None:
        row["project_id"] = str(row["project_id"])
    # Verify project ownership if linking to a project
    if data.project_id is not None:
        _verify_project_ownership(supabase, user_id, data.project_id)
    # Ensure content is a plain dict (not Pydantic model) for JSONB
    if "content" in row and hasattr(row["content"], "model_dump"):
        row["content"] = row["content"].model_dump(mode="json")
    result = supabase.table("diagrams").insert(row).execute()
    return result.data[0]


def list_diagrams(supabase: Client, user_id: UUID) -> list[dict]:
    result = (
        supabase.table("diagrams")
        .select(LIST_SELECT_FIELDS)
        .eq("user_id", str(user_id))
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data


def get_diagram(supabase: Client, user_id: UUID, diagram_id: UUID) -> dict:
    result = (
        supabase.table("diagrams")
        .select("*")
        .eq("id", str(diagram_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Diagram not found")
    return result.data[0]


def update_diagram(supabase: Client, user_id: UUID, diagram_id: UUID, data: DiagramUpdate) -> dict:
    """Partial update of a diagram. Only provided fields are updated.

    Addresses review concern: both reviewers flagged missing PATCH/update endpoint.
    """
    # Verify ownership first
    get_diagram(supabase, user_id, diagram_id)

    updates = data.model_dump(exclude_unset=True, mode="json")
    if not updates:
        # Nothing to update -- return current state
        return get_diagram(supabase, user_id, diagram_id)

    # Convert UUID fields to strings for Supabase
    if "project_id" in updates and updates["project_id"] is not None:
        updates["project_id"] = str(updates["project_id"])
    # Verify project ownership if linking to a (new) project
    if "project_id" in updates and updates["project_id"] is not None:
        _verify_project_ownership(supabase, user_id, UUID(updates["project_id"]))
    # Ensure content is a plain dict for JSONB
    if "content" in updates and hasattr(updates["content"], "model_dump"):
        updates["content"] = updates["content"].model_dump(mode="json")

    result = (
        supabase.table("diagrams")
        .update(updates)
        .eq("id", str(diagram_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    return result.data[0]


def delete_diagram(supabase: Client, user_id: UUID, diagram_id: UUID) -> None:
    get_diagram(supabase, user_id, diagram_id)
    supabase.table("diagrams").delete().eq("id", str(diagram_id)).eq(
        "user_id", str(user_id)
    ).execute()
