"""Validation node — runs entity validation rules on generated batches."""

import logging
from dataclasses import asdict

from app.agents.state import WorkflowState
from app.schemas.common import EntityType
from app.validation.engine import validate_entity

logger = logging.getLogger(__name__)

# Maps current_step values to the entity state keys
_STEP_TO_ENTITY: dict[str, tuple[EntityType, str, str]] = {
    "products_generated": (EntityType.product, "products", "product_errors"),
    "meters_generated": (EntityType.meter, "meters", "meter_errors"),
    "aggregations_generated": (EntityType.aggregation, "aggregations", "aggregation_errors"),
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

    entity_type, entities_key, errors_key = mapping
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

    step_name = entities_key.rstrip("s")  # "products" → "product"
    logger.info(
        "Validated %d %s entities: %d with errors",
        len(entities),
        step_name,
        len(all_errors),
    )

    return {
        errors_key: all_errors,
        "current_step": f"{step_name}s_validated",
    }
