"""Validation rules for m3ter AccountPlan entities."""

from app.validation.common import validate_custom_fields
from app.validation.engine import ValidationError


def validate(data: dict) -> list[ValidationError]:
    """Validate an account plan entity dict."""
    errors: list[ValidationError] = []

    # accountId — required
    if not data.get("accountId"):
        errors.append(
            ValidationError(field="accountId", message="accountId is required", severity="error")
        )
    elif not isinstance(data["accountId"], str):
        errors.append(
            ValidationError(
                field="accountId", message="accountId must be a string", severity="error"
            )
        )

    # planId — required
    if not data.get("planId"):
        errors.append(
            ValidationError(field="planId", message="planId is required", severity="error")
        )
    elif not isinstance(data["planId"], str):
        errors.append(
            ValidationError(field="planId", message="planId must be a string", severity="error")
        )

    # startDate — required, string
    if not data.get("startDate"):
        errors.append(
            ValidationError(field="startDate", message="startDate is required", severity="error")
        )
    elif not isinstance(data["startDate"], str):
        errors.append(
            ValidationError(
                field="startDate", message="startDate must be a string", severity="error"
            )
        )

    # endDate — optional, string if present
    end_date = data.get("endDate")
    if end_date is not None and not isinstance(end_date, str):
        errors.append(
            ValidationError(field="endDate", message="endDate must be a string", severity="error")
        )

    validate_custom_fields(data, errors)

    return errors
