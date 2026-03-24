"""Validation rules for m3ter Aggregation entities."""

from app.validation.common import VALID_ROUNDING_MODES, validate_code, validate_name
from app.validation.engine import ValidationError

VALID_AGGREGATION_TYPES = {
    "SUM",
    "MIN",
    "MAX",
    "COUNT",
    "LATEST",
    "MEAN",
    "CUSTOM",
    "UNIQUE",
    "CUSTOM_SQL",
}


def validate(data: dict) -> list[ValidationError]:
    """Validate an aggregation entity dict."""
    errors: list[ValidationError] = []

    validate_name(data, errors)
    validate_code(data, errors)

    # aggregation: required, valid enum
    agg_type = data.get("aggregation")
    if not agg_type:
        errors.append(
            ValidationError(
                field="aggregation",
                message="aggregation is required",
                severity="error",
            )
        )
    elif agg_type not in VALID_AGGREGATION_TYPES:
        errors.append(
            ValidationError(
                field="aggregation",
                message=(
                    f"invalid aggregation '{agg_type}'."
                    f" Must be one of: {', '.join(sorted(VALID_AGGREGATION_TYPES))}"
                ),
                severity="error",
            )
        )

    # targetField: required, string
    target_field = data.get("targetField")
    if not target_field:
        errors.append(
            ValidationError(
                field="targetField", message="targetField is required", severity="error"
            )
        )
    elif not isinstance(target_field, str):
        errors.append(
            ValidationError(
                field="targetField", message="targetField must be a string", severity="error"
            )
        )

    # rounding: optional, must be a string enum
    rounding = data.get("rounding")
    if rounding is not None:
        if not isinstance(rounding, str):
            errors.append(
                ValidationError(
                    field="rounding", message="rounding must be a string", severity="error"
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

    # quantityPerUnit: required, must be a positive number
    quantity_per_unit = data.get("quantityPerUnit")
    if quantity_per_unit is None:
        errors.append(
            ValidationError(
                field="quantityPerUnit",
                message="quantityPerUnit is required",
                severity="error",
            )
        )
    elif not isinstance(quantity_per_unit, (int, float)):
        errors.append(
            ValidationError(
                field="quantityPerUnit",
                message="quantityPerUnit must be a number",
                severity="error",
            )
        )
    elif quantity_per_unit <= 0:
        errors.append(
            ValidationError(
                field="quantityPerUnit",
                message="quantityPerUnit must be positive",
                severity="error",
            )
        )

    # unit: required, non-empty string
    unit = data.get("unit")
    if not unit:
        errors.append(ValidationError(field="unit", message="unit is required", severity="error"))
    elif not isinstance(unit, str):
        errors.append(
            ValidationError(field="unit", message="unit must be a string", severity="error")
        )

    # segmentedFields: optional, must be list of strings
    segmented = data.get("segmentedFields")
    if segmented is not None:
        if not isinstance(segmented, list):
            errors.append(
                ValidationError(
                    field="segmentedFields",
                    message="segmentedFields must be a list",
                    severity="error",
                )
            )
        else:
            for i, item in enumerate(segmented):
                if not isinstance(item, str):
                    errors.append(
                        ValidationError(
                            field=f"segmentedFields[{i}]",
                            message="each segmentedField must be a string",
                            severity="error",
                        )
                    )

    # segments: validate shape when present, warn when missing
    segments = data.get("segments")
    if segmented and isinstance(segmented, list) and len(segmented) > 0:
        if not segments:
            errors.append(
                ValidationError(
                    field="segments",
                    message=(
                        "segmentedFields defined without explicit segments; "
                        "wildcard segments will be used at push time"
                    ),
                    severity="warning",
                )
            )
    if segments is not None:
        if not isinstance(segments, list) or len(segments) == 0:
            errors.append(
                ValidationError(
                    field="segments",
                    message="segments must be a non-empty list",
                    severity="error",
                )
            )
        elif not all(isinstance(s, dict) for s in segments):
            errors.append(
                ValidationError(
                    field="segments",
                    message="each segment must be a dict mapping field codes to values",
                    severity="error",
                )
            )

    return errors
