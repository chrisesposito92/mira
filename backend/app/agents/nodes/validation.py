"""Validation node — runs entity validation rules on generated batches."""

import logging
from dataclasses import asdict

from app.agents.state import WorkflowState
from app.schemas.common import EntityType
from app.validation.cross_entity import validate_cross_entity
from app.validation.engine import validate_entity
from app.validation.rules import measurement as measurement_rules

logger = logging.getLogger(__name__)

# Maps current_step → (entity_type, entities_key, errors_key, validated_step)
_STEP_TO_ENTITY: dict[str, tuple[EntityType, str, str, str]] = {
    "products_generated": (
        EntityType.product,
        "products",
        "product_errors",
        "products_validated",
    ),
    "meters_generated": (
        EntityType.meter,
        "meters",
        "meter_errors",
        "meters_validated",
    ),
    "aggregations_generated": (
        EntityType.aggregation,
        "aggregations",
        "aggregation_errors",
        "aggregations_validated",
    ),
    "compound_aggregations_generated": (
        EntityType.compound_aggregation,
        "compound_aggregations",
        "compound_aggregation_errors",
        "compound_aggregations_validated",
    ),
    "plan_templates_generated": (
        EntityType.plan_template,
        "plan_templates",
        "plan_template_errors",
        "plan_templates_validated",
    ),
    "plans_generated": (
        EntityType.plan,
        "plans",
        "plan_errors",
        "plans_validated",
    ),
    "pricing_generated": (
        EntityType.pricing,
        "pricing",
        "pricing_errors",
        "pricing_validated",
    ),
    "accounts_generated": (
        EntityType.account,
        "accounts",
        "account_errors",
        "accounts_validated",
    ),
    "account_plans_generated": (
        EntityType.account_plan,
        "account_plans",
        "account_plan_errors",
        "account_plans_validated",
    ),
    "measurements_generated": (
        EntityType.measurement,
        "measurements",
        "measurement_errors",
        "measurements_validated",
    ),
}

# Maps step → (entity_type, context_keys) for cross-entity validation
_STEP_TO_CROSS_CONTEXT: dict[str, tuple[EntityType, tuple[str, ...]]] = {
    "account_plans_generated": (
        EntityType.account_plan,
        ("accounts", "approved_plans"),
    ),
    "measurements_generated": (
        EntityType.measurement,
        ("approved_meters", "approved_accounts"),
    ),
}


def _entity_display_name(entity: dict, entity_type: EntityType, index: int) -> str:
    """Build a human-readable display name for an entity in validation errors."""
    name = entity.get("name", "")
    if name:
        return name
    if entity_type == EntityType.pricing:
        pricing_type = entity.get("type", "pricing")
        desc = entity.get("description", "")
        return desc[:100] if desc else f"{pricing_type} pricing"
    if entity_type == EntityType.account_plan:
        account_id = entity.get("accountId", "")
        return f"AccountPlan: {account_id[:8]}" if account_id else f"AccountPlan {index}"
    if entity_type == EntityType.measurement:
        return entity.get("uid", f"Measurement {index}")
    return f"Entity {index}"


async def validate_entities(state: WorkflowState) -> dict:
    """Validate the current batch of entities based on current_step.

    Reads the appropriate entity list from state, runs validation rules
    on each entity, and stores structured errors in the corresponding
    error field.
    """
    current_step = state.get("current_step", "")
    mapping = _STEP_TO_ENTITY.get(current_step)

    if not mapping:
        logger.warning("validate_entities called with unexpected step: %s", current_step)
        return {}

    entity_type, entities_key, errors_key, validated_step = mapping
    entities = state.get(entities_key, [])

    all_errors: list[dict] = []
    for i, entity in enumerate(entities):
        errors = validate_entity(entity_type, entity)
        if errors:
            all_errors.append(
                {
                    "entity_index": i,
                    "entity_name": _entity_display_name(entity, entity_type, i),
                    "errors": [asdict(e) for e in errors],
                }
            )

    # Batch-level validation for measurements
    if entity_type == EntityType.measurement:
        batch_errors = measurement_rules.validate_batch(entities)
        if batch_errors:
            all_errors.append(
                {
                    "entity_index": -1,
                    "entity_name": "Batch",
                    "errors": [asdict(e) for e in batch_errors],
                }
            )

    # Cross-entity validation (referential integrity)
    cross_config = _STEP_TO_CROSS_CONTEXT.get(current_step)
    if cross_config:
        cross_entity_type, context_keys = cross_config
        context = {key: state.get(key, []) for key in context_keys}
        cross_errors = validate_cross_entity(cross_entity_type, entities, context)
        # Merge cross-entity errors with per-entity errors
        for cross_err in cross_errors:
            idx = cross_err["entity_index"]
            # Find existing error entry for this index or create a new one
            existing = next((e for e in all_errors if e["entity_index"] == idx), None)
            if existing:
                existing["errors"].extend(cross_err["errors"])
            else:
                all_errors.append(cross_err)

    logger.info(
        "Validated %d %s entities: %d with errors",
        len(entities),
        entity_type,
        len(all_errors),
    )

    return {
        errors_key: all_errors,
        "current_step": validated_step,
    }
