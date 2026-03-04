"""Validation rules for m3ter CompoundAggregation entities."""

from app.validation.common import validate_code, validate_custom_fields, validate_name
from app.validation.engine import ValidationError

VALID_ROUNDING_MODES = {"UP", "DOWN", "NEAREST", "NONE"}


def validate(data: dict) -> list[ValidationError]:
    """Validate a compound aggregation entity dict."""
    errors: list[ValidationError] = []

    validate_name(data, errors)
    validate_code(data, errors)

    # calculation: required, non-empty string
    calculation = data.get("calculation")
    if not calculation:
        errors.append(
            ValidationError(
                field="calculation",
                message="calculation is required",
                severity="error",
            )
        )
    elif not isinstance(calculation, str):
        errors.append(
            ValidationError(
                field="calculation",
                message="calculation must be a string",
                severity="error",
            )
        )

    # quantityPerUnit: required, numeric > 0
    qpu = data.get("quantityPerUnit")
    if qpu is None:
        errors.append(
            ValidationError(
                field="quantityPerUnit",
                message="quantityPerUnit is required",
                severity="error",
            )
        )
    elif not isinstance(qpu, (int, float)):
        errors.append(
            ValidationError(
                field="quantityPerUnit",
                message="quantityPerUnit must be numeric",
                severity="error",
            )
        )
    elif qpu <= 0:
        errors.append(
            ValidationError(
                field="quantityPerUnit",
                message="quantityPerUnit must be > 0",
                severity="error",
            )
        )

    # rounding: required, valid enum
    rounding = data.get("rounding")
    if not rounding:
        errors.append(
            ValidationError(
                field="rounding",
                message="rounding is required",
                severity="error",
            )
        )
    elif rounding not in VALID_ROUNDING_MODES:
        errors.append(
            ValidationError(
                field="rounding",
                message=(
                    f"invalid rounding '{rounding}'."
                    f" Must be one of: {', '.join(sorted(VALID_ROUNDING_MODES))}"
                ),
                severity="error",
            )
        )

    # unit: required, non-empty string
    unit = data.get("unit")
    if not unit:
        errors.append(
            ValidationError(
                field="unit",
                message="unit is required",
                severity="error",
            )
        )
    elif not isinstance(unit, str):
        errors.append(
            ValidationError(
                field="unit",
                message="unit must be a string",
                severity="error",
            )
        )

    # productId: optional, UUID format if present
    product_id = data.get("productId")
    if product_id is not None and not isinstance(product_id, str):
        errors.append(
            ValidationError(
                field="productId",
                message="productId must be a string (UUID)",
                severity="error",
            )
        )

    validate_custom_fields(data, errors)

    return errors
