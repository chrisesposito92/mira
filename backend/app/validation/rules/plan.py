"""Validation rules for m3ter Plan entities."""

from app.validation.common import (
    validate_code,
    validate_custom_fields,
    validate_name,
    validate_non_negative,
)
from app.validation.engine import ValidationError


def validate(data: dict) -> list[ValidationError]:
    """Validate a plan entity dict."""
    errors: list[ValidationError] = []

    validate_name(data, errors)
    validate_code(data, errors)

    # planTemplateId: required, string
    plan_template_id = data.get("planTemplateId")
    if not plan_template_id:
        errors.append(
            ValidationError(
                field="planTemplateId",
                message="planTemplateId is required",
                severity="error",
            )
        )
    elif not isinstance(plan_template_id, str):
        errors.append(
            ValidationError(
                field="planTemplateId",
                message="planTemplateId must be a string",
                severity="error",
            )
        )

    validate_non_negative(data, "standingCharge", errors)
    validate_non_negative(data, "minimumSpend", errors)
    validate_custom_fields(data, errors)

    return errors
