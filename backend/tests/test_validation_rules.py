"""Tests for entity validation rules — products, meters, aggregations."""

from app.schemas.common import EntityType
from app.validation.engine import validate_entity


class TestProductValidation:
    def test_valid_product_passes(self):
        data = {"name": "API Gateway", "code": "api_gateway"}
        errors = validate_entity(EntityType.product, data)
        assert len(errors) == 0

    def test_valid_product_with_custom_fields(self):
        data = {
            "name": "API Gateway",
            "code": "api_gateway",
            "customFields": {"tier": "standard"},
        }
        errors = validate_entity(EntityType.product, data)
        assert len(errors) == 0

    def test_missing_name_fails(self):
        data = {"code": "api_gateway"}
        errors = validate_entity(EntityType.product, data)
        error_fields = [e.field for e in errors]
        assert "name" in error_fields

    def test_missing_code_fails(self):
        data = {"name": "API Gateway"}
        errors = validate_entity(EntityType.product, data)
        error_fields = [e.field for e in errors]
        assert "code" in error_fields

    def test_bad_code_format_fails(self):
        data = {"name": "API Gateway", "code": "API-Gateway"}
        errors = validate_entity(EntityType.product, data)
        error_fields = [e.field for e in errors]
        assert "code" in error_fields

    def test_code_starting_with_number_fails(self):
        data = {"name": "API Gateway", "code": "1api_gateway"}
        errors = validate_entity(EntityType.product, data)
        error_fields = [e.field for e in errors]
        assert "code" in error_fields

    def test_name_too_long_fails(self):
        data = {"name": "x" * 201, "code": "api_gateway"}
        errors = validate_entity(EntityType.product, data)
        error_fields = [e.field for e in errors]
        assert "name" in error_fields

    def test_custom_fields_not_dict_fails(self):
        data = {"name": "API Gateway", "code": "api_gateway", "customFields": "invalid"}
        errors = validate_entity(EntityType.product, data)
        error_fields = [e.field for e in errors]
        assert "customFields" in error_fields

    def test_empty_data_has_both_errors(self):
        errors = validate_entity(EntityType.product, {})
        error_fields = [e.field for e in errors]
        assert "name" in error_fields
        assert "code" in error_fields


class TestMeterValidation:
    def _valid_meter(self) -> dict:
        return {
            "name": "API Request Meter",
            "code": "api_request_meter",
            "dataFields": [
                {"code": "request_count", "category": "MEASURE", "unit": "requests"},
            ],
        }

    def test_valid_meter_passes(self):
        errors = validate_entity(EntityType.meter, self._valid_meter())
        assert len(errors) == 0

    def test_missing_name_fails(self):
        data = self._valid_meter()
        del data["name"]
        errors = validate_entity(EntityType.meter, data)
        error_fields = [e.field for e in errors]
        assert "name" in error_fields

    def test_missing_code_fails(self):
        data = self._valid_meter()
        del data["code"]
        errors = validate_entity(EntityType.meter, data)
        error_fields = [e.field for e in errors]
        assert "code" in error_fields

    def test_no_data_fields_fails(self):
        data = {"name": "Test Meter", "code": "test_meter"}
        errors = validate_entity(EntityType.meter, data)
        error_fields = [e.field for e in errors]
        assert "dataFields" in error_fields

    def test_empty_data_fields_fails(self):
        data = {"name": "Test Meter", "code": "test_meter", "dataFields": []}
        errors = validate_entity(EntityType.meter, data)
        error_fields = [e.field for e in errors]
        assert "dataFields" in error_fields

    def test_duplicate_data_field_codes_fails(self):
        data = {
            "name": "Test Meter",
            "code": "test_meter",
            "dataFields": [
                {"code": "count", "category": "MEASURE"},
                {"code": "count", "category": "MEASURE"},
            ],
        }
        errors = validate_entity(EntityType.meter, data)
        assert any("duplicate" in e.message for e in errors)

    def test_invalid_category_fails(self):
        data = {
            "name": "Test Meter",
            "code": "test_meter",
            "dataFields": [
                {"code": "count", "category": "INVALID"},
            ],
        }
        errors = validate_entity(EntityType.meter, data)
        assert any("category" in e.field for e in errors)

    def test_derived_field_missing_calculation_fails(self):
        data = self._valid_meter()
        data["derivedFields"] = [{"code": "derived_field"}]
        errors = validate_entity(EntityType.meter, data)
        assert any("calculation" in e.field for e in errors)

    def test_derived_field_unreferenced_calculation_warns(self):
        data = self._valid_meter()
        data["derivedFields"] = [
            {"code": "derived", "calculation": "unrelated_field * 2"},
        ]
        errors = validate_entity(EntityType.meter, data)
        warnings = [e for e in errors if e.severity == "warning"]
        assert len(warnings) > 0

    def test_valid_derived_field_passes(self):
        data = self._valid_meter()
        data["derivedFields"] = [
            {"code": "doubled", "calculation": "request_count * 2"},
        ]
        errors = validate_entity(EntityType.meter, data)
        # No errors (may have warnings about referencing)
        actual_errors = [e for e in errors if e.severity == "error"]
        assert len(actual_errors) == 0


class TestAggregationValidation:
    def _valid_aggregation(self) -> dict:
        return {
            "name": "Daily API Requests",
            "code": "daily_api_requests",
            "aggregation": "SUM",
            "targetField": "request_count",
            "quantityPerUnit": 1.0,
            "unit": "requests",
        }

    def test_valid_aggregation_passes(self):
        errors = validate_entity(EntityType.aggregation, self._valid_aggregation())
        assert len(errors) == 0

    def test_valid_with_rounding(self):
        data = self._valid_aggregation()
        data["rounding"] = "UP"
        errors = validate_entity(EntityType.aggregation, data)
        assert len(errors) == 0

    def test_valid_with_segmented_fields(self):
        data = self._valid_aggregation()
        data["segmentedFields"] = ["region", "tier"]
        errors = validate_entity(EntityType.aggregation, data)
        # Only warnings expected (missing segments), no actual errors
        assert all(e.severity == "warning" for e in errors)

    def test_segmented_fields_with_segments_no_warnings(self):
        data = self._valid_aggregation()
        data["segmentedFields"] = ["region", "tier"]
        data["segments"] = [{"region": "*", "tier": "*"}]
        errors = validate_entity(EntityType.aggregation, data)
        assert len(errors) == 0

    def test_missing_name_fails(self):
        data = self._valid_aggregation()
        del data["name"]
        errors = validate_entity(EntityType.aggregation, data)
        assert any(e.field == "name" for e in errors)

    def test_missing_aggregation_type_fails(self):
        data = self._valid_aggregation()
        del data["aggregation"]
        errors = validate_entity(EntityType.aggregation, data)
        assert any(e.field == "aggregation" for e in errors)

    def test_invalid_aggregation_type_fails(self):
        data = self._valid_aggregation()
        data["aggregation"] = "AVERAGE"  # not a valid type
        errors = validate_entity(EntityType.aggregation, data)
        assert any(e.field == "aggregation" for e in errors)

    def test_missing_target_field_fails(self):
        data = self._valid_aggregation()
        del data["targetField"]
        errors = validate_entity(EntityType.aggregation, data)
        assert any(e.field == "targetField" for e in errors)

    def test_invalid_rounding_type_fails(self):
        data = self._valid_aggregation()
        data["rounding"] = "INVALID"
        errors = validate_entity(EntityType.aggregation, data)
        assert any(e.field == "rounding" for e in errors)

    def test_rounding_not_string_fails(self):
        data = self._valid_aggregation()
        data["rounding"] = 42
        errors = validate_entity(EntityType.aggregation, data)
        assert any(e.field == "rounding" for e in errors)

    def test_segmented_fields_not_list_fails(self):
        data = self._valid_aggregation()
        data["segmentedFields"] = "not_a_list"
        errors = validate_entity(EntityType.aggregation, data)
        assert any(e.field == "segmentedFields" for e in errors)

    def test_all_valid_aggregation_types_accepted(self):
        valid_types = [
            "SUM",
            "MIN",
            "MAX",
            "COUNT",
            "LATEST",
            "MEAN",
            "CUSTOM",
            "UNIQUE",
            "CUSTOM_SQL",
        ]
        for agg_type in valid_types:
            data = self._valid_aggregation()
            data["aggregation"] = agg_type
            errors = validate_entity(EntityType.aggregation, data)
            assert len(errors) == 0, f"{agg_type} should be valid"

    def test_empty_unit_fails(self):
        data = self._valid_aggregation()
        data["unit"] = ""
        errors = validate_entity(EntityType.aggregation, data)
        assert any(e.field == "unit" for e in errors)
