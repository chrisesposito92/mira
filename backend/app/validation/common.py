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
