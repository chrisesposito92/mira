"""Service layer for pushing entities to m3ter."""

import logging
from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from app.m3ter.client import M3terClient
from app.m3ter.encryption import decrypt_value
from app.m3ter.entities import BulkPushResult, PushResult, push_entities_ordered

logger = logging.getLogger(__name__)

# Statuses eligible for push
_PUSHABLE_STATUSES = {"approved", "push_failed"}


def _verify_use_case_ownership(supabase: Client, user_id: UUID, use_case_id: UUID) -> dict:
    """Verify use case ownership and return the use case row."""
    result = (
        supabase.table("use_cases")
        .select("id, project_id, projects!inner(user_id, org_connection_id)")
        .eq("id", str(use_case_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Use case not found")
    row = result.data[0]
    if row.get("projects", {}).get("user_id") != str(user_id):
        raise HTTPException(status_code=404, detail="Use case not found")
    return row


def _verify_object_ownership(supabase: Client, user_id: UUID, object_id: UUID) -> dict:
    """Verify object ownership and return the object row."""
    result = (
        supabase.table("generated_objects")
        .select("*, use_cases!inner(project_id, projects!inner(user_id, org_connection_id))")
        .eq("id", str(object_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Generated object not found")
    row = result.data[0]
    project_user_id = row.get("use_cases", {}).get("projects", {}).get("user_id")
    if project_user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Generated object not found")
    return row


async def _resolve_org_connection(
    supabase: Client,
    user_id: UUID,
    use_case_id: UUID,
) -> tuple[str, str, str, str]:
    """Resolve org connection credentials for a use case.

    Returns (org_id, api_url, client_id, client_secret).

    Raises HTTPException(400) if no org connection is linked.
    """
    uc_row = _verify_use_case_ownership(supabase, user_id, use_case_id)

    org_connection_id = uc_row.get("projects", {}).get("org_connection_id")
    if not org_connection_id:
        raise HTTPException(
            status_code=400,
            detail="No m3ter organization connection linked to this project",
        )

    conn_result = (
        supabase.table("org_connections").select("*").eq("id", str(org_connection_id)).execute()
    )
    if not conn_result.data:
        raise HTTPException(
            status_code=400,
            detail="Linked organization connection not found",
        )

    conn = conn_result.data[0]
    org_id = conn["org_id"]
    api_url = conn["api_url"]
    client_id = decrypt_value(conn["client_id"])
    client_secret = decrypt_value(conn["client_secret"])

    return org_id, api_url, client_id, client_secret


async def push_object(
    supabase: Client,
    user_id: UUID,
    object_id: UUID,
    on_progress: Callable[[PushResult], Any] | None = None,
) -> PushResult:
    """Push a single object to m3ter.

    Validates ownership and status (must be 'approved' or 'push_failed').
    """
    obj_row = _verify_object_ownership(supabase, user_id, object_id)

    # Strip join data for the push engine
    obj = {k: v for k, v in obj_row.items() if k != "use_cases"}

    if obj.get("status") not in _PUSHABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Object status must be 'approved' or 'push_failed', got '{obj.get('status')}'",
        )

    use_case_id = UUID(obj["use_case_id"])
    org_id, api_url, client_id, client_secret = await _resolve_org_connection(
        supabase, user_id, use_case_id
    )

    # Fetch already-pushed siblings for reference resolution (e.g. a meter
    # referencing a product's m3ter_id). Without these the resolver would fail
    # on any entity that has cross-entity references.
    pushed_siblings_result = (
        supabase.table("generated_objects")
        .select("*")
        .eq("use_case_id", str(use_case_id))
        .eq("status", "pushed")
        .execute()
    )
    pushed_siblings = pushed_siblings_result.data or []
    objects_for_engine = pushed_siblings + [obj]

    client = M3terClient(org_id, api_url, client_id, client_secret)
    try:
        bulk_result = await push_entities_ordered(client, supabase, objects_for_engine, on_progress)

        # Find the result for the target object (skip reference-only siblings)
        for r in bulk_result.results:
            if r.entity_id == str(object_id):
                return r

        if bulk_result.results:
            return bulk_result.results[0]

        return PushResult(
            entity_id=str(object_id),
            entity_type=obj.get("entity_type", ""),
            success=False,
            error="No results returned from push engine",
        )
    finally:
        await client.close()


async def push_use_case_objects(
    supabase: Client,
    user_id: UUID,
    use_case_id: UUID,
    object_ids: list[UUID] | None = None,
    on_progress: Callable[[PushResult], Any] | None = None,
) -> BulkPushResult:
    """Push all eligible objects for a use case to m3ter.

    Fetches objects with status 'approved' or 'push_failed', optionally filtered
    by object_ids. Also includes already-pushed objects for reference resolution.
    """
    org_id, api_url, client_id, client_secret = await _resolve_org_connection(
        supabase, user_id, use_case_id
    )

    # Fetch all objects for the use case (including pushed, for reference resolution)
    all_objects_result = (
        supabase.table("generated_objects")
        .select("*")
        .eq("use_case_id", str(use_case_id))
        .execute()
    )
    all_objects = all_objects_result.data or []

    # Filter to eligible objects (plus already-pushed for reference resolution)
    if object_ids:
        str_ids = {str(oid) for oid in object_ids}
        objects_to_push = [
            o
            for o in all_objects
            if (str(o["id"]) in str_ids and o.get("status") in _PUSHABLE_STATUSES)
            or o.get("status") == "pushed"
        ]
    else:
        objects_to_push = [
            o
            for o in all_objects
            if o.get("status") in _PUSHABLE_STATUSES or o.get("status") == "pushed"
        ]

    if not objects_to_push:
        return BulkPushResult(total=0)

    client = M3terClient(org_id, api_url, client_id, client_secret)
    try:
        return await push_entities_ordered(client, supabase, objects_to_push, on_progress)
    finally:
        await client.close()


def get_push_status(
    supabase: Client,
    user_id: UUID,
    use_case_id: UUID,
) -> dict[str, Any]:
    """Get push readiness info for a use case.

    Returns org connection status, eligible/pushed/total counts,
    and per-entity-type breakdown.
    """
    uc_row = _verify_use_case_ownership(supabase, user_id, use_case_id)

    # Check org connection
    org_connection_id = uc_row.get("projects", {}).get("org_connection_id")
    org_connected = bool(org_connection_id)

    # Fetch all objects
    objects_result = (
        supabase.table("generated_objects")
        .select("*")
        .eq("use_case_id", str(use_case_id))
        .execute()
    )
    all_objects = objects_result.data or []

    total_count = len(all_objects)
    eligible_count = sum(1 for o in all_objects if o.get("status") in _PUSHABLE_STATUSES)
    pushed_count = sum(1 for o in all_objects if o.get("status") == "pushed")

    # Per-entity-type breakdown
    entity_breakdown: dict[str, dict[str, int]] = {}
    for obj in all_objects:
        et = obj.get("entity_type", "unknown")
        if et not in entity_breakdown:
            entity_breakdown[et] = {"eligible": 0, "pushed": 0, "total": 0}
        entity_breakdown[et]["total"] += 1
        if obj.get("status") in _PUSHABLE_STATUSES:
            entity_breakdown[et]["eligible"] += 1
        if obj.get("status") == "pushed":
            entity_breakdown[et]["pushed"] += 1

    return {
        "org_connected": org_connected,
        "eligible_count": eligible_count,
        "pushed_count": pushed_count,
        "total_count": total_count,
        "entity_breakdown": entity_breakdown,
    }
