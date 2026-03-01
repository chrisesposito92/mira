"""Validation rules for m3ter Pricing entities."""

from app.validation.common import (
    validate_code_format,
    validate_custom_fields,
    validate_non_negative,
)
from app.validation.engine import ValidationError

VALID_PRICING_TYPES = {"DEBIT", "PRODUCT_CREDIT", "GLOBAL_CREDIT"}


def _validate_pricing_bands(
    bands: list[dict],
    field_name: str,
    errors: list[ValidationError],
) -> None:
    """Validate a list of pricing bands (shared between pricingBands and overagePricingBands)."""
    prev_lower_limit: float | None = None
    for i, band in enumerate(bands):
        prefix = f"{field_name}[{i}]"
        if not isinstance(band, dict):
            errors.append(
                ValidationError(
                    field=prefix,
                    message="each pricing band must be a dict",
                    severity="error",
                )
            )
            continue

        # lowerLimit: required, numeric, >= 0
        lower_limit = band.get("lowerLimit")
        if lower_limit is None:
            errors.append(
                ValidationError(
                    field=f"{prefix}.lowerLimit",
                    message="lowerLimit is required",
                    severity="error",
                )
            )
        elif not isinstance(lower_limit, (int, float)):
            errors.append(
                ValidationError(
                    field=f"{prefix}.lowerLimit",
                    message="lowerLimit must be numeric",
                    severity="error",
                )
            )
        else:
            if lower_limit < 0:
                errors.append(
                    ValidationError(
                        field=f"{prefix}.lowerLimit",
                        message="lowerLimit must be >= 0",
                        severity="error",
                    )
                )
            # Check strictly ascending order
            if prev_lower_limit is not None and lower_limit <= prev_lower_limit:
                errors.append(
                    ValidationError(
                        field=f"{prefix}.lowerLimit",
                        message=("pricing bands must have strictly ascending lowerLimit values"),
                        severity="warning",
                    )
                )
            prev_lower_limit = lower_limit

        # Must have at least fixedPrice or unitPrice
        fixed_price = band.get("fixedPrice")
        unit_price = band.get("unitPrice")
        has_fixed = isinstance(fixed_price, (int, float))
        has_unit = isinstance(unit_price, (int, float))
        if not has_fixed and not has_unit:
            errors.append(
                ValidationError(
                    field=prefix,
                    message="each band must have at least fixedPrice or unitPrice (numeric)",
                    severity="error",
                )
            )


def validate(data: dict) -> list[ValidationError]:
    """Validate a pricing entity dict."""
    errors: list[ValidationError] = []

    # planId or planTemplateId: warning if neither is present
    plan_id = data.get("planId")
    plan_template_id = data.get("planTemplateId")
    if not plan_id and not plan_template_id:
        errors.append(
            ValidationError(
                field="planId",
                message="either planId or planTemplateId should be provided",
                severity="warning",
            )
        )

    # type: optional, if present must be one of valid values
    pricing_type = data.get("type")
    if pricing_type is not None and pricing_type not in VALID_PRICING_TYPES:
        errors.append(
            ValidationError(
                field="type",
                message=(
                    f"invalid type '{pricing_type}'."
                    f" Must be one of: {', '.join(sorted(VALID_PRICING_TYPES))}"
                ),
                severity="error",
            )
        )

    # startDate: required, string
    start_date = data.get("startDate")
    if not start_date:
        errors.append(
            ValidationError(field="startDate", message="startDate is required", severity="error")
        )
    elif not isinstance(start_date, str):
        errors.append(
            ValidationError(
                field="startDate", message="startDate must be a string", severity="error"
            )
        )

    # pricingBands: required, list with >= 1 item
    pricing_bands = data.get("pricingBands")
    if pricing_bands is None:
        errors.append(
            ValidationError(
                field="pricingBands", message="pricingBands is required", severity="error"
            )
        )
    elif not isinstance(pricing_bands, list):
        errors.append(
            ValidationError(
                field="pricingBands", message="pricingBands must be a list", severity="error"
            )
        )
    elif len(pricing_bands) < 1:
        errors.append(
            ValidationError(
                field="pricingBands",
                message="pricingBands must contain at least 1 item",
                severity="error",
            )
        )
    else:
        _validate_pricing_bands(pricing_bands, "pricingBands", errors)

    # overagePricingBands: optional, same structure validation
    overage_bands = data.get("overagePricingBands")
    if overage_bands is not None:
        if not isinstance(overage_bands, list):
            errors.append(
                ValidationError(
                    field="overagePricingBands",
                    message="overagePricingBands must be a list",
                    severity="error",
                )
            )
        elif len(overage_bands) < 1:
            errors.append(
                ValidationError(
                    field="overagePricingBands",
                    message="overagePricingBands must contain at least 1 item",
                    severity="error",
                )
            )
        else:
            _validate_pricing_bands(overage_bands, "overagePricingBands", errors)

    # description: optional, max 200 chars
    description = data.get("description")
    if description is not None:
        if not isinstance(description, str):
            errors.append(
                ValidationError(
                    field="description",
                    message="description must be a string",
                    severity="error",
                )
            )
        elif len(description) > 200:
            errors.append(
                ValidationError(
                    field="description",
                    message="description must be 200 characters or fewer",
                    severity="error",
                )
            )

    validate_non_negative(data, "minimumSpend", errors)
    validate_custom_fields(data, errors)

    # cumulative: optional, must be bool if present
    cumulative = data.get("cumulative")
    if cumulative is not None and not isinstance(cumulative, bool):
        errors.append(
            ValidationError(
                field="cumulative",
                message="cumulative must be a boolean",
                severity="error",
            )
        )

    # code: optional, validate format if present (but not required)
    validate_code_format(data, errors)

    return errors
