"""Tests for compound aggregation validation rules."""

from app.schemas.common import EntityType
from app.validation.engine import validate_entity


def _valid_compound_agg() -> dict:
    return {
        "name": "Billable Requests After Free Allowance",
        "code": "billable_requests_after_free",
        "calculation": "sum_requests - (max_apps * 100)",
        "quantityPerUnit": 1.0,
        "rounding": "UP",
        "unit": "requests",
    }


def test_valid_compound_aggregation():
    errors = validate_entity(EntityType.compound_aggregation, _valid_compound_agg())
    assert errors == []


def test_missing_required_fields():
    errors = validate_entity(EntityType.compound_aggregation, {})
    fields = {e.field for e in errors}
    assert "name" in fields
    assert "code" in fields
    assert "calculation" in fields
    assert "quantityPerUnit" in fields
    assert "rounding" in fields
    assert "unit" in fields


def test_invalid_code_format():
    data = _valid_compound_agg()
    data["code"] = "Invalid-Code"
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert any(e.field == "code" for e in errors)


def test_invalid_rounding():
    data = _valid_compound_agg()
    data["rounding"] = "INVALID"
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert any(e.field == "rounding" for e in errors)


def test_quantity_per_unit_must_be_positive():
    data = _valid_compound_agg()
    data["quantityPerUnit"] = 0
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert any(e.field == "quantityPerUnit" for e in errors)

    data["quantityPerUnit"] = -1
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert any(e.field == "quantityPerUnit" for e in errors)


def test_calculation_must_be_string():
    data = _valid_compound_agg()
    data["calculation"] = 123
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert any(e.field == "calculation" for e in errors)


def test_optional_product_id():
    data = _valid_compound_agg()
    data["productId"] = "some-uuid-string"
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert errors == []


def test_invalid_product_id_type():
    data = _valid_compound_agg()
    data["productId"] = 123
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert any(e.field == "productId" for e in errors)


def test_invalid_custom_fields():
    data = _valid_compound_agg()
    data["customFields"] = "not-a-dict"
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert any(e.field == "customFields" for e in errors)


def test_rounding_none_is_valid():
    data = _valid_compound_agg()
    data["rounding"] = "NONE"
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert errors == []


def test_evaluate_null_aggregations_true():
    data = _valid_compound_agg()
    data["evaluateNullAggregations"] = True
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert errors == []


def test_evaluate_null_aggregations_false():
    data = _valid_compound_agg()
    data["evaluateNullAggregations"] = False
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert errors == []


def test_evaluate_null_aggregations_invalid_type():
    data = _valid_compound_agg()
    data["evaluateNullAggregations"] = "yes"
    errors = validate_entity(EntityType.compound_aggregation, data)
    assert any(e.field == "evaluateNullAggregations" for e in errors)
