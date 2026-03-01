"""Service layer for generated_objects CRUD."""

import functools
from dataclasses import asdict
from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from app.agents.tools.m3ter_schema import get_schema
from app.schemas.common import EntityType
from app.schemas.generated_objects import CreateGeneratedObject, GeneratedObjectUpdate
from app.validation.engine import validate_entity


def list_objects(
    supabase: Client,
    user_id: UUID,
    use_case_id: UUID,
    entity_type: str | None = None,
    status: str | None = None,
) -> list[dict]:
    # Verify ownership through use_case → project chain
    _verify_use_case_ownership(supabase, user_id, use_case_id)

    query = supabase.table("generated_objects").select("*").eq("use_case_id", str(use_case_id))
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
    existing = get_object(supabase, user_id, object_id)

    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return existing

    result = (
        supabase.table("generated_objects")
        .update(updates)
        .eq("id", str(object_id))
        .eq("use_case_id", existing["use_case_id"])
        .execute()
    )
    return result.data[0]


def bulk_update_status(supabase: Client, user_id: UUID, ids: list[UUID], status: str) -> list[dict]:
    # Verify ownership of each object and collect use_case_ids for defense-in-depth
    verified_use_case_ids: set[str] = set()
    for obj_id in ids:
        obj = get_object(supabase, user_id, obj_id)
        verified_use_case_ids.add(obj["use_case_id"])

    str_ids = [str(i) for i in ids]
    result = (
        supabase.table("generated_objects")
        .update({"status": status})
        .in_("id", str_ids)
        .in_("use_case_id", list(verified_use_case_ids))
        .execute()
    )
    return result.data


def create_object(
    supabase: Client,
    user_id: UUID,
    use_case_id: UUID,
    data: CreateGeneratedObject,
) -> dict:
    """Create a new generated object with validation."""
    _verify_use_case_ownership(supabase, user_id, use_case_id)

    errors = validate_entity(data.entity_type, data.data or {})
    validation_errors = [asdict(e) for e in errors]

    obj_data = data.data or {}
    obj_name = data.name or obj_data.get("name") or data.entity_type.replace("_", " ").title()

    row = {
        "use_case_id": str(use_case_id),
        "entity_type": data.entity_type,
        "name": obj_name,
        "code": data.code,
        "status": "draft",
        "data": obj_data,
        "validation_errors": validation_errors or None,
    }
    result = supabase.table("generated_objects").insert(row).execute()
    return result.data[0]


@functools.cache
def generate_template(entity_type: EntityType) -> dict:
    """Generate a default template for an entity type from its schema."""
    try:
        schema = get_schema(entity_type)
    except ValueError:
        return {}

    def _default_value(field_def: dict) -> object:
        ftype = field_def.get("type", "str")
        if ftype == "str":
            return ""
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        if ftype == "dict":
            return {}
        if ftype == "list[str]":
            return []
        if ftype == "list[dict]":
            item_schema = field_def.get("item_schema", {})
            if item_schema:
                return [{k: _default_value(v) for k, v in item_schema.items()}]
            return [{}]
        return ""

    template: dict = {}
    for field_name, field_def in schema.items():
        is_required = field_def.get("required", False)
        is_name_or_code = field_name in ("name", "code")
        if is_required or is_name_or_code:
            template[field_name] = _default_value(field_def)

    return template


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
