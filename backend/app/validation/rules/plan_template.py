"""Validation rules for m3ter PlanTemplate entities."""

import re

from app.validation.common import (
    validate_code,
    validate_custom_fields,
    validate_name,
    validate_non_negative,
)
from app.validation.engine import ValidationError

VALID_BILL_FREQUENCIES = {"DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC", "MIXED"}
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


def validate(data: dict) -> list[ValidationError]:
    """Validate a plan template entity dict."""
    errors: list[ValidationError] = []

    validate_name(data, errors)
    validate_code(data, errors)

    # productId: required, string
    product_id = data.get("productId")
    if not product_id:
        errors.append(
            ValidationError(field="productId", message="productId is required", severity="error")
        )
    elif not isinstance(product_id, str):
        errors.append(
            ValidationError(
                field="productId", message="productId must be a string", severity="error"
            )
        )

    # currency: required, 3-char uppercase ISO string
    currency = data.get("currency")
    if not currency:
        errors.append(
            ValidationError(field="currency", message="currency is required", severity="error")
        )
    elif not isinstance(currency, str):
        errors.append(
            ValidationError(field="currency", message="currency must be a string", severity="error")
        )
    elif not CURRENCY_PATTERN.match(currency):
        errors.append(
            ValidationError(
                field="currency",
                message="currency must be a 3-character uppercase ISO code (e.g., USD, EUR)",
                severity="error",
            )
        )

    # billFrequency: required, must be one of valid values
    bill_frequency = data.get("billFrequency")
    if not bill_frequency:
        errors.append(
            ValidationError(
                field="billFrequency", message="billFrequency is required", severity="error"
            )
        )
    elif bill_frequency not in VALID_BILL_FREQUENCIES:
        errors.append(
            ValidationError(
                field="billFrequency",
                message=(
                    f"invalid billFrequency '{bill_frequency}'."
                    f" Must be one of: {', '.join(sorted(VALID_BILL_FREQUENCIES))}"
                ),
                severity="error",
            )
        )

    validate_non_negative(data, "standingCharge", errors, required=True)

    # billFrequencyInterval: optional, if present must be int 1-365
    bill_freq_interval = data.get("billFrequencyInterval")
    if bill_freq_interval is not None:
        if not isinstance(bill_freq_interval, int):
            errors.append(
                ValidationError(
                    field="billFrequencyInterval",
                    message="billFrequencyInterval must be an integer",
                    severity="error",
                )
            )
        elif bill_freq_interval < 1 or bill_freq_interval > 365:
            errors.append(
                ValidationError(
                    field="billFrequencyInterval",
                    message="billFrequencyInterval must be between 1 and 365",
                    severity="error",
                )
            )

    validate_non_negative(data, "minimumSpend", errors)
    validate_custom_fields(data, errors)

    return errors
