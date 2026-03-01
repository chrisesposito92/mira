"""Unit tests for plan_template, plan, and pricing validation rules."""

from app.schemas.common import EntityType
from app.validation.engine import ValidationError, validate_entity

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_plan_template() -> dict:
    return {
        "name": "Standard Plan Template",
        "code": "standard_plan_template",
        "productId": "prod-123",
        "currency": "USD",
        "billFrequency": "MONTHLY",
        "standingCharge": 10.0,
    }


def _valid_plan() -> dict:
    return {
        "name": "Standard Plan",
        "code": "standard_plan",
        "planTemplateId": "pt-123",
    }


def _valid_pricing() -> dict:
    return {
        "startDate": "2024-01-01",
        "planId": "plan-123",
        "pricingBands": [{"lowerLimit": 0, "unitPrice": 0.01}],
    }


def _errors_for(entity_type: EntityType, data: dict) -> list[ValidationError]:
    return validate_entity(entity_type, data)


def _error_fields(errors: list[ValidationError]) -> list[str]:
    return [e.field for e in errors]


def _severity_map(errors: list[ValidationError]) -> dict[str, str]:
    return {e.field: e.severity for e in errors}


# ===========================================================================
# PlanTemplate tests (~12)
# ===========================================================================


class TestPlanTemplateValidation:
    def test_valid_plan_template_passes(self) -> None:
        errors = _errors_for(EntityType.plan_template, _valid_plan_template())
        assert errors == []

    def test_missing_name(self) -> None:
        data = _valid_plan_template()
        del data["name"]
        errors = _errors_for(EntityType.plan_template, data)
        assert "name" in _error_fields(errors)

    def test_missing_code(self) -> None:
        data = _valid_plan_template()
        del data["code"]
        errors = _errors_for(EntityType.plan_template, data)
        assert "code" in _error_fields(errors)

    def test_missing_product_id(self) -> None:
        data = _valid_plan_template()
        del data["productId"]
        errors = _errors_for(EntityType.plan_template, data)
        assert "productId" in _error_fields(errors)

    def test_missing_currency(self) -> None:
        data = _valid_plan_template()
        del data["currency"]
        errors = _errors_for(EntityType.plan_template, data)
        assert "currency" in _error_fields(errors)

    def test_invalid_currency_lowercase(self) -> None:
        data = _valid_plan_template()
        data["currency"] = "usd"
        errors = _errors_for(EntityType.plan_template, data)
        assert "currency" in _error_fields(errors)

    def test_invalid_currency_wrong_length(self) -> None:
        data = _valid_plan_template()
        data["currency"] = "US"
        errors = _errors_for(EntityType.plan_template, data)
        assert "currency" in _error_fields(errors)

    def test_missing_bill_frequency(self) -> None:
        data = _valid_plan_template()
        del data["billFrequency"]
        errors = _errors_for(EntityType.plan_template, data)
        assert "billFrequency" in _error_fields(errors)

    def test_invalid_bill_frequency(self) -> None:
        data = _valid_plan_template()
        data["billFrequency"] = "BIWEEKLY"
        errors = _errors_for(EntityType.plan_template, data)
        assert "billFrequency" in _error_fields(errors)

    def test_missing_standing_charge(self) -> None:
        data = _valid_plan_template()
        del data["standingCharge"]
        errors = _errors_for(EntityType.plan_template, data)
        assert "standingCharge" in _error_fields(errors)

    def test_negative_standing_charge(self) -> None:
        data = _valid_plan_template()
        data["standingCharge"] = -5.0
        errors = _errors_for(EntityType.plan_template, data)
        assert "standingCharge" in _error_fields(errors)

    def test_bill_frequency_interval_out_of_range(self) -> None:
        data = _valid_plan_template()
        data["billFrequencyInterval"] = 0
        errors = _errors_for(EntityType.plan_template, data)
        assert "billFrequencyInterval" in _error_fields(errors)

        data["billFrequencyInterval"] = 366
        errors = _errors_for(EntityType.plan_template, data)
        assert "billFrequencyInterval" in _error_fields(errors)

    def test_minimum_spend_negative(self) -> None:
        data = _valid_plan_template()
        data["minimumSpend"] = -1.0
        errors = _errors_for(EntityType.plan_template, data)
        assert "minimumSpend" in _error_fields(errors)

    def test_custom_fields_not_dict(self) -> None:
        data = _valid_plan_template()
        data["customFields"] = "not a dict"
        errors = _errors_for(EntityType.plan_template, data)
        assert "customFields" in _error_fields(errors)


# ===========================================================================
# Plan tests (~8)
# ===========================================================================


class TestPlanValidation:
    def test_valid_plan_passes(self) -> None:
        errors = _errors_for(EntityType.plan, _valid_plan())
        assert errors == []

    def test_missing_name(self) -> None:
        data = _valid_plan()
        del data["name"]
        errors = _errors_for(EntityType.plan, data)
        assert "name" in _error_fields(errors)

    def test_missing_code(self) -> None:
        data = _valid_plan()
        del data["code"]
        errors = _errors_for(EntityType.plan, data)
        assert "code" in _error_fields(errors)

    def test_missing_plan_template_id(self) -> None:
        data = _valid_plan()
        del data["planTemplateId"]
        errors = _errors_for(EntityType.plan, data)
        assert "planTemplateId" in _error_fields(errors)

    def test_standing_charge_negative(self) -> None:
        data = _valid_plan()
        data["standingCharge"] = -10.0
        errors = _errors_for(EntityType.plan, data)
        assert "standingCharge" in _error_fields(errors)

    def test_minimum_spend_negative(self) -> None:
        data = _valid_plan()
        data["minimumSpend"] = -5.0
        errors = _errors_for(EntityType.plan, data)
        assert "minimumSpend" in _error_fields(errors)

    def test_custom_fields_not_dict(self) -> None:
        data = _valid_plan()
        data["customFields"] = [1, 2, 3]
        errors = _errors_for(EntityType.plan, data)
        assert "customFields" in _error_fields(errors)

    def test_valid_with_optional_overrides(self) -> None:
        data = _valid_plan()
        data["standingCharge"] = 25.0
        data["minimumSpend"] = 100.0
        data["customFields"] = {"tier": "enterprise"}
        errors = _errors_for(EntityType.plan, data)
        assert errors == []


# ===========================================================================
# Pricing tests (~20)
# ===========================================================================


class TestPricingValidation:
    def test_valid_pricing_passes(self) -> None:
        errors = _errors_for(EntityType.pricing, _valid_pricing())
        assert errors == []

    def test_missing_start_date(self) -> None:
        data = _valid_pricing()
        del data["startDate"]
        errors = _errors_for(EntityType.pricing, data)
        assert "startDate" in _error_fields(errors)

    def test_missing_pricing_bands(self) -> None:
        data = _valid_pricing()
        del data["pricingBands"]
        errors = _errors_for(EntityType.pricing, data)
        assert "pricingBands" in _error_fields(errors)

    def test_empty_pricing_bands(self) -> None:
        data = _valid_pricing()
        data["pricingBands"] = []
        errors = _errors_for(EntityType.pricing, data)
        assert "pricingBands" in _error_fields(errors)

    def test_band_missing_lower_limit(self) -> None:
        data = _valid_pricing()
        data["pricingBands"] = [{"unitPrice": 0.01}]
        errors = _errors_for(EntityType.pricing, data)
        assert "pricingBands[0].lowerLimit" in _error_fields(errors)

    def test_band_negative_lower_limit(self) -> None:
        data = _valid_pricing()
        data["pricingBands"] = [{"lowerLimit": -1, "unitPrice": 0.01}]
        errors = _errors_for(EntityType.pricing, data)
        assert "pricingBands[0].lowerLimit" in _error_fields(errors)

    def test_band_missing_both_prices(self) -> None:
        data = _valid_pricing()
        data["pricingBands"] = [{"lowerLimit": 0}]
        errors = _errors_for(EntityType.pricing, data)
        assert "pricingBands[0]" in _error_fields(errors)

    def test_bands_not_sorted_warning(self) -> None:
        data = _valid_pricing()
        data["pricingBands"] = [
            {"lowerLimit": 100, "unitPrice": 0.005},
            {"lowerLimit": 0, "unitPrice": 0.01},
        ]
        errors = _errors_for(EntityType.pricing, data)
        sev = _severity_map(errors)
        assert sev.get("pricingBands[1].lowerLimit") == "warning"

    def test_no_plan_id_or_plan_template_id_warning(self) -> None:
        data = _valid_pricing()
        del data["planId"]
        errors = _errors_for(EntityType.pricing, data)
        sev = _severity_map(errors)
        assert sev.get("planId") == "warning"

    def test_invalid_type(self) -> None:
        data = _valid_pricing()
        data["type"] = "INVALID"
        errors = _errors_for(EntityType.pricing, data)
        assert "type" in _error_fields(errors)

    def test_overage_pricing_bands_validation(self) -> None:
        data = _valid_pricing()
        data["overagePricingBands"] = [{"lowerLimit": -1, "unitPrice": 0.02}]
        errors = _errors_for(EntityType.pricing, data)
        assert "overagePricingBands[0].lowerLimit" in _error_fields(errors)

    def test_description_too_long(self) -> None:
        data = _valid_pricing()
        data["description"] = "x" * 201
        errors = _errors_for(EntityType.pricing, data)
        assert "description" in _error_fields(errors)

    def test_minimum_spend_negative(self) -> None:
        data = _valid_pricing()
        data["minimumSpend"] = -10.0
        errors = _errors_for(EntityType.pricing, data)
        assert "minimumSpend" in _error_fields(errors)

    def test_cumulative_not_bool(self) -> None:
        data = _valid_pricing()
        data["cumulative"] = "yes"
        errors = _errors_for(EntityType.pricing, data)
        assert "cumulative" in _error_fields(errors)

    def test_valid_flat_pricing(self) -> None:
        """Flat pricing: single band starting at 0 with a unitPrice."""
        data = _valid_pricing()
        data["pricingBands"] = [{"lowerLimit": 0, "unitPrice": 0.05}]
        errors = _errors_for(EntityType.pricing, data)
        assert errors == []

    def test_valid_tiered_pricing(self) -> None:
        """Tiered pricing: multiple bands with ascending lowerLimits."""
        data = _valid_pricing()
        data["pricingBands"] = [
            {"lowerLimit": 0, "unitPrice": 0.10},
            {"lowerLimit": 100, "unitPrice": 0.08},
            {"lowerLimit": 1000, "unitPrice": 0.05},
        ]
        errors = _errors_for(EntityType.pricing, data)
        assert errors == []

    def test_valid_volume_pricing(self) -> None:
        """Volume pricing: bands with fixedPrice and unitPrice."""
        data = _valid_pricing()
        data["pricingBands"] = [
            {"lowerLimit": 0, "fixedPrice": 0, "unitPrice": 0.10},
            {"lowerLimit": 500, "fixedPrice": 10.0, "unitPrice": 0.07},
        ]
        errors = _errors_for(EntityType.pricing, data)
        assert errors == []

    def test_valid_stairstep_pricing(self) -> None:
        """Stairstep pricing: bands with only fixedPrice (no unitPrice)."""
        data = _valid_pricing()
        data["pricingBands"] = [
            {"lowerLimit": 0, "fixedPrice": 10.0},
            {"lowerLimit": 100, "fixedPrice": 25.0},
            {"lowerLimit": 500, "fixedPrice": 50.0},
        ]
        errors = _errors_for(EntityType.pricing, data)
        assert errors == []

    def test_valid_counter_pricing(self) -> None:
        """Counter pricing: single band with 0 unitPrice (free events counted)."""
        data = _valid_pricing()
        data["pricingBands"] = [{"lowerLimit": 0, "unitPrice": 0}]
        errors = _errors_for(EntityType.pricing, data)
        assert errors == []

    def test_valid_pricing_with_code(self) -> None:
        """Pricing with an optional code that passes validate_code."""
        data = _valid_pricing()
        data["code"] = "api_usage_pricing"
        errors = _errors_for(EntityType.pricing, data)
        assert errors == []

    def test_invalid_code_on_pricing(self) -> None:
        """Pricing with an invalid code should produce an error."""
        data = _valid_pricing()
        data["code"] = "Invalid-Code"
        errors = _errors_for(EntityType.pricing, data)
        assert "code" in _error_fields(errors)
