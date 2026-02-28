"""Entity validation engine — dispatches to per-entity rule modules."""

from dataclasses import dataclass
from typing import Literal

from app.schemas.common import EntityType


@dataclass
class ValidationError:
    field: str
    message: str
    severity: Literal["error", "warning"]


def validate_entity(entity_type: EntityType, data: dict) -> list[ValidationError]:
    """Validate an entity dict against its rules. Returns list of errors/warnings."""
    from app.validation.rules import aggregation, meter, product

    validators = {
        EntityType.product: product.validate,
        EntityType.meter: meter.validate,
        EntityType.aggregation: aggregation.validate,
    }
    validator = validators.get(entity_type)
    if not validator:
        return [
            ValidationError(
                field="entity_type",
                message=f"No validator for {entity_type}",
                severity="error",
            )
        ]
    return validator(data)
