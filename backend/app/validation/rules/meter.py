"""Validation rules for m3ter Meter entities."""

from app.validation.common import validate_code, validate_name
from app.validation.engine import ValidationError

VALID_CATEGORIES = {"WHO", "WHAT", "WHERE", "MEASURE", "METADATA", "OTHER", "INCOME", "COST"}


def validate(data: dict) -> list[ValidationError]:
    """Validate a meter entity dict."""
    errors: list[ValidationError] = []

    validate_name(data, errors)
    validate_code(data, errors)

    # dataFields: required, list with at least 1 item
    data_fields = data.get("dataFields")
    if data_fields is None:
        errors.append(
            ValidationError(field="dataFields", message="dataFields is required", severity="error")
        )
    elif not isinstance(data_fields, list):
        errors.append(
            ValidationError(
                field="dataFields", message="dataFields must be a list", severity="error"
            )
        )
    elif len(data_fields) < 1:
        errors.append(
            ValidationError(
                field="dataFields",
                message="dataFields must contain at least 1 item",
                severity="error",
            )
        )
    else:
        seen_codes: set[str] = set()
        valid_data_field_codes: set[str] = set()
        for i, field in enumerate(data_fields):
            prefix = f"dataFields[{i}]"
            if not isinstance(field, dict):
                errors.append(
                    ValidationError(
                        field=prefix, message="each dataField must be a dict", severity="error"
                    )
                )
                continue

            # code: required string
            field_code = field.get("code")
            if not field_code:
                errors.append(
                    ValidationError(
                        field=f"{prefix}.code", message="code is required", severity="error"
                    )
                )
            elif not isinstance(field_code, str):
                errors.append(
                    ValidationError(
                        field=f"{prefix}.code",
                        message="code must be a string",
                        severity="error",
                    )
                )
            else:
                valid_data_field_codes.add(field_code)
                if field_code in seen_codes:
                    errors.append(
                        ValidationError(
                            field=f"{prefix}.code",
                            message=f"duplicate dataField code: '{field_code}'",
                            severity="error",
                        )
                    )
                seen_codes.add(field_code)

            # category: required, valid enum
            category = field.get("category")
            if not category:
                errors.append(
                    ValidationError(
                        field=f"{prefix}.category",
                        message="category is required",
                        severity="error",
                    )
                )
            elif category not in VALID_CATEGORIES:
                errors.append(
                    ValidationError(
                        field=f"{prefix}.category",
                        message=(
                            f"invalid category '{category}'."
                            f" Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
                        ),
                        severity="error",
                    )
                )

        # derivedFields: optional validation
        derived_fields = data.get("derivedFields")
        if derived_fields is not None:
            if not isinstance(derived_fields, list):
                errors.append(
                    ValidationError(
                        field="derivedFields",
                        message="derivedFields must be a list",
                        severity="error",
                    )
                )
            else:
                for i, dfield in enumerate(derived_fields):
                    prefix = f"derivedFields[{i}]"
                    if not isinstance(dfield, dict):
                        errors.append(
                            ValidationError(
                                field=prefix,
                                message="each derivedField must be a dict",
                                severity="error",
                            )
                        )
                        continue

                    # code: required
                    if not dfield.get("code"):
                        errors.append(
                            ValidationError(
                                field=f"{prefix}.code",
                                message="code is required",
                                severity="error",
                            )
                        )

                    # calculation: required
                    calc = dfield.get("calculation")
                    if not calc:
                        errors.append(
                            ValidationError(
                                field=f"{prefix}.calculation",
                                message="calculation is required",
                                severity="error",
                            )
                        )
                    elif isinstance(calc, str) and valid_data_field_codes:
                        # Warn if calculation doesn't reference any known data field codes
                        references_any = any(code in calc for code in valid_data_field_codes)
                        if not references_any:
                            errors.append(
                                ValidationError(
                                    field=f"{prefix}.calculation",
                                    message=(
                                        f"calculation '{calc}' does not reference"
                                        " any known dataField codes"
                                    ),
                                    severity="warning",
                                )
                            )

    return errors
