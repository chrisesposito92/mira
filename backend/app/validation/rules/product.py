"""Validation rules for m3ter Product entities."""

from app.validation.common import validate_code, validate_custom_fields, validate_name
from app.validation.engine import ValidationError


def validate(data: dict) -> list[ValidationError]:
    """Validate a product entity dict."""
    errors: list[ValidationError] = []

    validate_name(data, errors)
    validate_code(data, errors)
    validate_custom_fields(data, errors)

    return errors
