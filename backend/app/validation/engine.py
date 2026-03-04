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
    from app.validation.rules import (
        account,
        account_plan,
        aggregation,
        compound_aggregation,
        measurement,
        meter,
        plan,
        plan_template,
        pricing,
        product,
    )

    validators = {
        EntityType.product: product.validate,
        EntityType.meter: meter.validate,
        EntityType.aggregation: aggregation.validate,
        EntityType.compound_aggregation: compound_aggregation.validate,
        EntityType.plan_template: plan_template.validate,
        EntityType.plan: plan.validate,
        EntityType.pricing: pricing.validate,
        EntityType.account: account.validate,
        EntityType.account_plan: account_plan.validate,
        EntityType.measurement: measurement.validate,
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
