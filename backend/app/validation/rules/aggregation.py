"""Validation rules for m3ter Aggregation entities."""

from app.validation.common import validate_code, validate_name
from app.validation.engine import ValidationError

VALID_AGGREGATION_TYPES = {"SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "CUSTOM"}
VALID_ROUNDING_TYPES = {"UP", "DOWN", "NEAREST"}


def validate(data: dict) -> list[ValidationError]:
    """Validate an aggregation entity dict."""
    errors: list[ValidationError] = []

    validate_name(data, errors)
    validate_code(data, errors)

    # aggregationType: required, valid enum
    agg_type = data.get("aggregationType")
    if not agg_type:
        errors.append(
            ValidationError(
                field="aggregationType",
                message="aggregationType is required",
                severity="error",
            )
        )
    elif agg_type not in VALID_AGGREGATION_TYPES:
        errors.append(
            ValidationError(
                field="aggregationType",
                message=(
                    f"invalid aggregationType '{agg_type}'."
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

    # rounding: optional, must have precision (int) and roundingType (valid enum)
    rounding = data.get("rounding")
    if rounding is not None:
        if not isinstance(rounding, dict):
            errors.append(
                ValidationError(
                    field="rounding", message="rounding must be a dict", severity="error"
                )
            )
        else:
            precision = rounding.get("precision")
            if precision is None:
                errors.append(
                    ValidationError(
                        field="rounding.precision",
                        message="precision is required in rounding",
                        severity="error",
                    )
                )
            elif not isinstance(precision, int):
                errors.append(
                    ValidationError(
                        field="rounding.precision",
                        message="precision must be an integer",
                        severity="error",
                    )
                )

            rounding_type = rounding.get("roundingType")
            if not rounding_type:
                errors.append(
                    ValidationError(
                        field="rounding.roundingType",
                        message="roundingType is required in rounding",
                        severity="error",
                    )
                )
            elif rounding_type not in VALID_ROUNDING_TYPES:
                errors.append(
                    ValidationError(
                        field="rounding.roundingType",
                        message=(
                            f"invalid roundingType '{rounding_type}'."
                            f" Must be one of: {', '.join(sorted(VALID_ROUNDING_TYPES))}"
                        ),
                        severity="error",
                    )
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

    return errors
