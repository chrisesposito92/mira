"""Validation node — runs entity validation rules on generated batches."""

import logging
from dataclasses import asdict

from app.agents.state import WorkflowState
from app.schemas.common import EntityType
from app.validation.engine import validate_entity

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
}


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
                    "entity_name": entity.get("name", f"Entity {i}"),
                    "errors": [asdict(e) for e in errors],
                }
            )

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
