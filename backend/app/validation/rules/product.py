"""Validation rules for m3ter Product entities."""

from app.validation.common import validate_code, validate_name
from app.validation.engine import ValidationError


def validate(data: dict) -> list[ValidationError]:
    """Validate a product entity dict."""
    errors: list[ValidationError] = []

    validate_name(data, errors)
    validate_code(data, errors)

    # customFields: optional, must be dict if present
    custom_fields = data.get("customFields")
    if custom_fields is not None and not isinstance(custom_fields, dict):
        errors.append(
            ValidationError(
                field="customFields",
                message="customFields must be a dict",
                severity="error",
            )
        )

    return errors
