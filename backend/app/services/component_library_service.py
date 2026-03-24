"""Service layer for component library queries."""

from uuid import UUID

from fastapi import HTTPException
from supabase import Client


def list_components(supabase: Client) -> list[dict]:
    result = supabase.table("component_library").select("*").order("display_order").execute()
    return result.data


def get_component(supabase: Client, component_id: UUID) -> dict:
    result = supabase.table("component_library").select("*").eq("id", str(component_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Component not found")
    return result.data[0]
