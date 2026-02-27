"""Service layer for use_cases CRUD."""

from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from app.schemas.use_cases import UseCaseCreate, UseCaseUpdate
from app.services.project_service import get_project


def create_use_case(supabase: Client, user_id: UUID, project_id: UUID, data: UseCaseCreate) -> dict:
    # Verify project ownership
    get_project(supabase, user_id, project_id)

    row = {
        "project_id": str(project_id),
        **data.model_dump(exclude_unset=True),
    }
    # Serialize date to string
    if "contract_start_date" in row and row["contract_start_date"] is not None:
        row["contract_start_date"] = row["contract_start_date"].isoformat()

    result = supabase.table("use_cases").insert(row).execute()
    return result.data[0]


def list_use_cases(supabase: Client, user_id: UUID, project_id: UUID) -> list[dict]:
    get_project(supabase, user_id, project_id)
    result = (
        supabase.table("use_cases")
        .select("*")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_use_case(supabase: Client, user_id: UUID, use_case_id: UUID) -> dict:
    result = (
        supabase.table("use_cases")
        .select("*, projects!inner(user_id)")
        .eq("id", str(use_case_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Use case not found")
    row = result.data[0]
    if row.get("projects", {}).get("user_id") != str(user_id):
        raise HTTPException(status_code=404, detail="Use case not found")
    return {k: v for k, v in row.items() if k != "projects"}


def update_use_case(
    supabase: Client, user_id: UUID, use_case_id: UUID, data: UseCaseUpdate
) -> dict:
    existing = get_use_case(supabase, user_id, use_case_id)

    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return existing

    if "contract_start_date" in updates and updates["contract_start_date"] is not None:
        updates["contract_start_date"] = updates["contract_start_date"].isoformat()

    result = (
        supabase.table("use_cases")
        .update(updates)
        .eq("id", str(use_case_id))
        .eq("project_id", existing["project_id"])
        .execute()
    )
    return result.data[0]


def delete_use_case(supabase: Client, user_id: UUID, use_case_id: UUID) -> None:
    existing = get_use_case(supabase, user_id, use_case_id)
    supabase.table("use_cases").delete().eq("id", str(use_case_id)).eq(
        "project_id", existing["project_id"]
    ).execute()
