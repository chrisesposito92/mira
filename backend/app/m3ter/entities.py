"""Reference resolution and ordered entity push engine for m3ter."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from supabase import Client

from app.m3ter.client import M3terClient
from app.m3ter.mapper import map_entity_to_m3ter_payload, map_measurements_to_m3ter_payload
from app.schemas.common import EntityType

logger = logging.getLogger(__name__)

# Canonical push order — no compound_aggregation, no measurement (submitted separately)
PUSH_ORDER: list[EntityType] = [
    EntityType.product,
    EntityType.meter,
    EntityType.aggregation,
    EntityType.plan_template,
    EntityType.plan,
    EntityType.pricing,
    EntityType.account,
    EntityType.account_plan,
]

# Index for O(1) sort-key lookups
_PUSH_ORDER_INDEX: dict[EntityType, int] = {et: i for i, et in enumerate(PUSH_ORDER)}

# Maps reference field names to the entity type they point to
REFERENCE_FIELDS: dict[str, EntityType] = {
    "productId": EntityType.product,
    "meterId": EntityType.meter,
    "aggregationId": EntityType.aggregation,
    "planTemplateId": EntityType.plan_template,
    "planId": EntityType.plan,
    "accountId": EntityType.account,
    "parentAccountId": EntityType.account,
}


class ReferenceResolutionError(Exception):
    """Raised when a reference field points to an entity that hasn't been pushed yet."""

    def __init__(self, field_name: str, referenced_id: str, message: str):
        self.field = field_name
        self.referenced_id = referenced_id
        self.message = message
        super().__init__(message)


@dataclass
class PushResult:
    """Result of pushing a single entity to m3ter."""

    entity_id: str
    entity_type: str
    success: bool
    m3ter_id: str | None = None
    error: str | None = None


@dataclass
class BulkPushResult:
    """Result of a bulk push operation."""

    results: list[PushResult] = field(default_factory=list)
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0


class ReferenceResolver:
    """Resolves MIRA entity UUIDs to m3ter UUIDs for reference fields."""

    def __init__(self) -> None:
        self._id_map: dict[str, str] = {}

    def register(self, mira_id: str, m3ter_id: str) -> None:
        """Register a mapping from MIRA UUID to m3ter UUID."""
        self._id_map[mira_id] = m3ter_id

    def preload_from_db(self, pushed_objects: list[dict[str, Any]]) -> None:
        """Pre-load mappings from already-pushed objects.

        Objects must have status='pushed' and a non-null m3ter_id.
        """
        for obj in pushed_objects:
            if obj.get("status") == "pushed" and obj.get("m3ter_id"):
                self._id_map[str(obj["id"])] = obj["m3ter_id"]

    def resolve_references(self, entity_type: EntityType, data: dict[str, Any]) -> dict[str, Any]:
        """Replace MIRA UUIDs with m3ter UUIDs in reference fields.

        Returns a new dict with resolved references.

        Raises:
            ReferenceResolutionError: If a referenced entity hasn't been pushed yet.
        """
        resolved = dict(data)

        for field_name, target_type in REFERENCE_FIELDS.items():
            if field_name not in resolved:
                continue
            mira_id = resolved[field_name]
            if mira_id is None:
                continue
            if mira_id in self._id_map:
                resolved[field_name] = self._id_map[mira_id]
            else:
                raise ReferenceResolutionError(
                    field_name=field_name,
                    referenced_id=mira_id,
                    message=(
                        f"Cannot resolve {field_name}={mira_id}: "
                        f"referenced {target_type} has not been pushed yet"
                    ),
                )

        return resolved


def _sort_key(entity_type_str: str) -> int:
    """Sort key based on PUSH_ORDER. Measurement goes last."""
    try:
        et = EntityType(entity_type_str)
    except ValueError:
        return len(PUSH_ORDER) + 1

    if et == EntityType.measurement:
        return len(PUSH_ORDER)

    return _PUSH_ORDER_INDEX.get(et, len(PUSH_ORDER) + 1)


async def _push_single_entity(
    client: M3terClient,
    entity_type: EntityType,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Push a single entity to m3ter, calling the appropriate client method."""
    if entity_type == EntityType.product:
        return await client.create_product(payload)
    elif entity_type == EntityType.meter:
        return await client.create_meter(payload)
    elif entity_type == EntityType.aggregation:
        return await client.create_aggregation(payload)
    elif entity_type == EntityType.plan_template:
        return await client.create_plan_template(payload)
    elif entity_type == EntityType.plan:
        return await client.create_plan(payload)
    elif entity_type == EntityType.pricing:
        # Pricing requires either planId or planTemplateId in URL path
        plan_m3ter_id = payload.get("planId")
        plan_template_m3ter_id = payload.get("planTemplateId")
        if plan_m3ter_id:
            return await client.create_pricing(plan_m3ter_id, payload)
        elif plan_template_m3ter_id:
            return await client.create_pricing_on_template(plan_template_m3ter_id, payload)
        else:
            raise ValueError("Pricing entity must have a resolved planId or planTemplateId")
    elif entity_type == EntityType.account:
        return await client.create_account(payload)
    elif entity_type == EntityType.account_plan:
        return await client.create_account_plan(payload)
    elif entity_type == EntityType.measurement:
        return await client.submit_measurements([payload])
    else:
        raise ValueError(f"Unsupported entity type for push: {entity_type}")


async def push_entities_ordered(
    client: M3terClient,
    supabase: Client,
    objects: list[dict[str, Any]],
    on_progress: Callable[[PushResult], Awaitable[None] | None] | None = None,
) -> BulkPushResult:
    """Push entities to m3ter in dependency order.

    1. Pre-load resolver from already-pushed objects
    2. Sort by PUSH_ORDER
    3. Skip already-pushed objects
    4. For each: resolve refs → map payload → push → update DB → register
    5. On failure: stop remaining pushes, mark as skipped
    """
    result = BulkPushResult(total=len(objects))
    resolver = ReferenceResolver()

    # Pre-load from already-pushed objects
    resolver.preload_from_db(objects)

    # Sort by entity type push order
    sorted_objects = sorted(objects, key=lambda o: _sort_key(o.get("entity_type", "")))

    failed = False
    for obj in sorted_objects:
        entity_id = str(obj["id"])
        entity_type_str = obj.get("entity_type", "")

        # Skip already-pushed
        if obj.get("status") == "pushed":
            result.skipped += 1
            push_result = PushResult(
                entity_id=entity_id,
                entity_type=entity_type_str,
                success=True,
                m3ter_id=obj.get("m3ter_id"),
            )
            result.results.append(push_result)
            if on_progress:
                await _call_progress(on_progress, push_result)
            continue

        # If a previous push failed, skip remaining
        if failed:
            result.skipped += 1
            push_result = PushResult(
                entity_id=entity_id,
                entity_type=entity_type_str,
                success=False,
                error="Skipped due to previous failure",
            )
            result.results.append(push_result)
            if on_progress:
                await _call_progress(on_progress, push_result)
            continue

        try:
            entity_type = EntityType(entity_type_str)
            data = obj.get("data", {})

            # Resolve references
            resolved_data = resolver.resolve_references(entity_type, data)

            # Map payload
            if entity_type == EntityType.measurement:
                payloads = map_measurements_to_m3ter_payload([resolved_data])
                payload = payloads[0] if payloads else resolved_data
            else:
                payload = map_entity_to_m3ter_payload(entity_type, resolved_data)

            # Push to m3ter
            response = await _push_single_entity(client, entity_type, payload)

            # Extract m3ter_id from response
            m3ter_id = response.get("id") if isinstance(response, dict) else None

            # Update DB
            now = datetime.now(UTC).isoformat()
            db_result = (
                supabase.table("generated_objects")
                .update({"status": "pushed", "m3ter_id": m3ter_id, "updated_at": now})
                .eq("id", entity_id)
                .execute()
            )
            if not db_result.data:
                logger.error(
                    "DB update returned no rows for entity %s — status may not be 'pushed'",
                    entity_id,
                )

            # Register in resolver
            if m3ter_id:
                resolver.register(entity_id, m3ter_id)

            result.succeeded += 1
            push_result = PushResult(
                entity_id=entity_id,
                entity_type=entity_type_str,
                success=True,
                m3ter_id=m3ter_id,
            )
            result.results.append(push_result)
            if on_progress:
                await _call_progress(on_progress, push_result)

        except Exception as exc:
            logger.exception("Failed to push entity %s (%s)", entity_id, entity_type_str)

            # Update DB with failure
            now = datetime.now(UTC).isoformat()
            supabase.table("generated_objects").update(
                {"status": "push_failed", "updated_at": now}
            ).eq("id", entity_id).execute()

            result.failed += 1
            push_result = PushResult(
                entity_id=entity_id,
                entity_type=entity_type_str,
                success=False,
                error=str(exc),
            )
            result.results.append(push_result)
            if on_progress:
                await _call_progress(on_progress, push_result)

            # Stop remaining pushes
            failed = True

    return result


async def _call_progress(
    on_progress: Callable[[PushResult], Awaitable[None] | None],
    push_result: PushResult,
) -> None:
    """Call a progress callback, supporting both sync and async callables."""
    ret = on_progress(push_result)
    if asyncio.iscoroutine(ret) or asyncio.isfuture(ret):
        await ret
