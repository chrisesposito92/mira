"""Shared validation helpers for common entity fields."""

import re

from app.validation.engine import ValidationError

CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_name(data: dict, errors: list[ValidationError]) -> None:
    """Validate the 'name' field: required, string, 1-200 chars."""
    name = data.get("name")
    if not name:
        errors.append(ValidationError(field="name", message="name is required", severity="error"))
    elif not isinstance(name, str):
        errors.append(
            ValidationError(field="name", message="name must be a string", severity="error")
        )
    elif len(name) > 200:
        errors.append(
            ValidationError(
                field="name",
                message="name must be 200 characters or fewer",
                severity="error",
            )
        )


def validate_code(data: dict, errors: list[ValidationError]) -> None:
    """Validate the 'code' field: required, string, lowercase snake_case."""
    code = data.get("code")
    if not code:
        errors.append(ValidationError(field="code", message="code is required", severity="error"))
    elif not isinstance(code, str):
        errors.append(
            ValidationError(field="code", message="code must be a string", severity="error")
        )
    elif not CODE_PATTERN.match(code):
        errors.append(
            ValidationError(
                field="code",
                message=(
                    "code must be lowercase, start with a letter,"
                    " and contain only letters, digits, and underscores"
                ),
                severity="error",
            )
        )


def validate_code_format(data: dict, errors: list[ValidationError]) -> None:
    """Validate code format only (not required). Use for optional code fields."""
    code = data.get("code")
    if code is None:
        return
    if not isinstance(code, str):
        errors.append(
            ValidationError(field="code", message="code must be a string", severity="error")
        )
    elif code and not CODE_PATTERN.match(code):
        errors.append(
            ValidationError(
                field="code",
                message=(
                    "code must be lowercase alphanumeric with underscores, starting with a letter"
                ),
                severity="error",
            )
        )


def validate_custom_fields(data: dict, errors: list[ValidationError]) -> None:
    """Validate the optional 'customFields' field: must be dict if present."""
    custom_fields = data.get("customFields")
    if custom_fields is not None and not isinstance(custom_fields, dict):
        errors.append(
            ValidationError(
                field="customFields",
                message="customFields must be a dict",
                severity="error",
            )
        )


def validate_non_negative(
    data: dict,
    field_name: str,
    errors: list[ValidationError],
    *,
    required: bool = False,
) -> None:
    """Validate a numeric field is >= 0. Optionally required."""
    value = data.get(field_name)
    if value is None:
        if required:
            errors.append(
                ValidationError(
                    field=field_name, message=f"{field_name} is required", severity="error"
                )
            )
        return
    if not isinstance(value, (int, float)):
        errors.append(
            ValidationError(
                field=field_name, message=f"{field_name} must be numeric", severity="error"
            )
        )
    elif value < 0:
        errors.append(
            ValidationError(
                field=field_name, message=f"{field_name} must be >= 0", severity="error"
            )
        )
