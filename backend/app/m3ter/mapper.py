"""Allowlist-based payload mapper: MIRA objects → m3ter API payloads."""

from typing import Any

from app.agents.tools.m3ter_schema import (
    ACCOUNT_PLAN_SCHEMA,
    ACCOUNT_SCHEMA,
    AGGREGATION_SCHEMA,
    MEASUREMENT_SCHEMA,
    METER_SCHEMA,
    PLAN_SCHEMA,
    PLAN_TEMPLATE_SCHEMA,
    PRICING_SCHEMA,
    PRODUCT_SCHEMA,
)
from app.schemas.common import EntityType

# Allowlisted fields per entity type, derived from m3ter_schema.py
_ALLOWED_FIELDS: dict[EntityType, set[str]] = {
    EntityType.product: set(PRODUCT_SCHEMA.keys()),
    EntityType.meter: set(METER_SCHEMA.keys()),
    EntityType.aggregation: set(AGGREGATION_SCHEMA.keys()),
    EntityType.plan_template: set(PLAN_TEMPLATE_SCHEMA.keys()),
    EntityType.plan: set(PLAN_SCHEMA.keys()),
    EntityType.pricing: set(PRICING_SCHEMA.keys()),
    EntityType.account: set(ACCOUNT_SCHEMA.keys()),
    EntityType.account_plan: set(ACCOUNT_PLAN_SCHEMA.keys()),
    EntityType.measurement: set(MEASUREMENT_SCHEMA.keys()),
}

# Internal fields that should always be stripped before sending to m3ter
_INTERNAL_FIELDS = {"id", "index"}


def map_entity_to_m3ter_payload(entity_type: EntityType, data: dict[str, Any]) -> dict[str, Any]:
    """Map a MIRA entity data dict to a clean m3ter API payload.

    - Strips internal fields (id, index)
    - Filters to allowlisted fields only
    - Removes None values
    """
    allowed = _ALLOWED_FIELDS.get(entity_type)
    if allowed is None:
        raise ValueError(f"No field allowlist for entity type: {entity_type}")

    payload: dict[str, Any] = {}
    for key, value in data.items():
        if key in _INTERNAL_FIELDS:
            continue
        if key not in allowed:
            continue
        if value is None:
            continue
        payload[key] = value

    # m3ter API requires derivedFields to be present (at least []) for meters
    if entity_type == EntityType.meter and "derivedFields" not in payload:
        payload["derivedFields"] = []

    # m3ter API requires segments when segmentedFields is present
    if entity_type == EntityType.aggregation:
        seg_fields = payload.get("segmentedFields")
        if (
            seg_fields
            and not payload.get("segments")
            and isinstance(seg_fields, list)
            and all(isinstance(f, str) for f in seg_fields)
        ):
            # Auto-generate a single wildcard segment combining all fields:
            # m3ter dynamically creates segments as data arrives
            payload["segments"] = [{field: "*" for field in seg_fields}]

    return payload


def map_measurements_to_m3ter_payload(measurements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map a list of MIRA measurement dicts to m3ter Ingest API payloads.

    Measurements use entity codes (not UUIDs) and go through the Ingest API.
    """
    return [map_entity_to_m3ter_payload(EntityType.measurement, m) for m in measurements]
