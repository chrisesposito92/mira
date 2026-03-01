"""Validation rules for m3ter Measurement entities."""

import re

from app.validation.engine import ValidationError

_ISO_8601_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})$")


def validate(data: dict) -> list[ValidationError]:
    """Validate a single measurement entity dict."""
    errors: list[ValidationError] = []

    # uid — required
    uid = data.get("uid")
    if not uid:
        errors.append(ValidationError(field="uid", message="uid is required", severity="error"))
    elif not isinstance(uid, str):
        errors.append(
            ValidationError(field="uid", message="uid must be a string", severity="error")
        )

    # meter — required (code, not UUID)
    meter = data.get("meter")
    if not meter:
        errors.append(
            ValidationError(field="meter", message="meter code is required", severity="error")
        )
    elif not isinstance(meter, str):
        errors.append(
            ValidationError(field="meter", message="meter must be a string", severity="error")
        )

    # account — required (code, not UUID)
    account = data.get("account")
    if not account:
        errors.append(
            ValidationError(field="account", message="account code is required", severity="error")
        )
    elif not isinstance(account, str):
        errors.append(
            ValidationError(field="account", message="account must be a string", severity="error")
        )

    # ts — required, ISO 8601 format
    ts = data.get("ts")
    if not ts:
        errors.append(ValidationError(field="ts", message="ts is required", severity="error"))
    elif not isinstance(ts, str):
        errors.append(ValidationError(field="ts", message="ts must be a string", severity="error"))
    elif not _ISO_8601_PATTERN.match(ts):
        errors.append(
            ValidationError(
                field="ts",
                message="ts must be in ISO 8601 format (e.g., 2024-01-15T10:30:00Z)",
                severity="error",
            )
        )

    # end_ts — optional, ISO 8601 if present
    end_ts = data.get("end_ts")
    if end_ts is not None:
        if not isinstance(end_ts, str):
            errors.append(
                ValidationError(field="end_ts", message="end_ts must be a string", severity="error")
            )
        elif not _ISO_8601_PATTERN.match(end_ts):
            errors.append(
                ValidationError(
                    field="end_ts",
                    message="end_ts must be in ISO 8601 format",
                    severity="error",
                )
            )

    # data — required, dict with numeric values
    measurement_data = data.get("data")
    if measurement_data is None:
        errors.append(ValidationError(field="data", message="data is required", severity="error"))
    elif not isinstance(measurement_data, dict):
        errors.append(
            ValidationError(field="data", message="data must be a dict", severity="error")
        )
    else:
        for key, value in measurement_data.items():
            if not isinstance(value, (int, float)):
                errors.append(
                    ValidationError(
                        field=f"data.{key}",
                        message=f"data.{key} must be numeric",
                        severity="error",
                    )
                )

    return errors


def validate_batch(measurements: list[dict]) -> list[ValidationError]:
    """Validate batch-level constraints for a list of measurements."""
    errors: list[ValidationError] = []

    if len(measurements) > 1000:
        errors.append(
            ValidationError(
                field="batch",
                message=f"Batch size {len(measurements)} exceeds limit of 1000",
                severity="error",
            )
        )

    # Check for duplicate UIDs
    uids = [m.get("uid") for m in measurements if m.get("uid")]
    seen: set[str] = set()
    for uid in uids:
        if uid in seen:
            errors.append(
                ValidationError(
                    field="uid",
                    message=f"Duplicate uid: {uid}",
                    severity="error",
                )
            )
        seen.add(uid)

    return errors
