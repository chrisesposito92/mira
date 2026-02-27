"""Service layer for org_connections CRUD + connection testing."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from app.m3ter.client import M3terClient
from app.m3ter.encryption import decrypt_value, encrypt_value
from app.schemas.org_connections import OrgConnectionCreate, OrgConnectionUpdate


async def create_org_connection(supabase: Client, user_id: UUID, data: OrgConnectionCreate) -> dict:
    row = {
        "user_id": str(user_id),
        "org_id": data.org_id,
        "org_name": data.org_name,
        "api_url": data.api_url,
        "client_id": encrypt_value(data.client_id),
        "client_secret": encrypt_value(data.client_secret),
    }
    result = supabase.table("org_connections").insert(row).execute()
    return _strip_secrets(result.data[0])


def list_org_connections(supabase: Client, user_id: UUID) -> list[dict]:
    result = (
        supabase.table("org_connections")
        .select("*")
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .execute()
    )
    return [_strip_secrets(r) for r in result.data]


def get_org_connection(supabase: Client, user_id: UUID, connection_id: UUID) -> dict:
    result = (
        supabase.table("org_connections")
        .select("*")
        .eq("id", str(connection_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Org connection not found")
    return _strip_secrets(result.data[0])


def update_org_connection(
    supabase: Client, user_id: UUID, connection_id: UUID, data: OrgConnectionUpdate
) -> dict:
    get_org_connection(supabase, user_id, connection_id)

    updates = data.model_dump(exclude_unset=True)
    if "client_id" in updates and updates["client_id"] is not None:
        updates["client_id"] = encrypt_value(updates["client_id"])
    else:
        updates.pop("client_id", None)
    if "client_secret" in updates and updates["client_secret"] is not None:
        updates["client_secret"] = encrypt_value(updates["client_secret"])
    else:
        updates.pop("client_secret", None)

    if not updates:
        return get_org_connection(supabase, user_id, connection_id)

    result = (
        supabase.table("org_connections")
        .update(updates)
        .eq("id", str(connection_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    return _strip_secrets(result.data[0])


def delete_org_connection(supabase: Client, user_id: UUID, connection_id: UUID) -> None:
    get_org_connection(supabase, user_id, connection_id)

    supabase.table("org_connections").delete().eq("id", str(connection_id)).eq(
        "user_id", str(user_id)
    ).execute()


async def test_org_connection(supabase: Client, user_id: UUID, connection_id: UUID) -> dict:
    # Get the full row including encrypted credential columns
    result = (
        supabase.table("org_connections")
        .select("*")
        .eq("id", str(connection_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Org connection not found")
    row = result.data[0]

    client_id = decrypt_value(row["client_id"])
    client_secret = decrypt_value(row["client_secret"])

    m3ter = M3terClient(
        org_id=row["org_id"],
        api_url=row["api_url"],
        client_id=client_id,
        client_secret=client_secret,
    )
    test_result = await m3ter.test_connection()

    now = datetime.now(UTC).isoformat()
    new_status = "active" if test_result["success"] else "error"
    supabase.table("org_connections").update({"status": new_status, "last_tested_at": now}).eq(
        "id", str(connection_id)
    ).execute()

    return test_result


def _strip_secrets(row: dict) -> dict:
    """Remove encrypted credential columns from response."""
    row.pop("client_id", None)
    row.pop("client_secret", None)
    return row
