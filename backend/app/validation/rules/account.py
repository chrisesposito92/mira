"""Validation rules for m3ter Account entities."""

import re

from app.validation.common import (
    validate_code,
    validate_custom_fields,
    validate_name,
    validate_non_negative,
)
from app.validation.engine import ValidationError

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate(data: dict) -> list[ValidationError]:
    """Validate an account entity dict."""
    errors: list[ValidationError] = []

    validate_name(data, errors)
    validate_code(data, errors)

    # emailAddress — required, basic format check
    email = data.get("emailAddress")
    if not email:
        errors.append(
            ValidationError(
                field="emailAddress", message="emailAddress is required", severity="error"
            )
        )
    elif not isinstance(email, str):
        errors.append(
            ValidationError(
                field="emailAddress", message="emailAddress must be a string", severity="error"
            )
        )
    elif not _EMAIL_PATTERN.match(email):
        errors.append(
            ValidationError(
                field="emailAddress",
                message="emailAddress must be a valid email address",
                severity="error",
            )
        )

    # currency — optional, 3-char uppercase ISO
    currency = data.get("currency")
    if currency is not None:
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isupper():
            errors.append(
                ValidationError(
                    field="currency",
                    message="currency must be a 3-character uppercase ISO code (e.g., USD)",
                    severity="error",
                )
            )

    # address — optional, must be dict
    address = data.get("address")
    if address is not None and not isinstance(address, dict):
        errors.append(
            ValidationError(field="address", message="address must be a dict", severity="error")
        )

    # daysBeforeBillDue — optional, non-negative
    validate_non_negative(data, "daysBeforeBillDue", errors)

    validate_custom_fields(data, errors)

    return errors
