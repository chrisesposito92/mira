"""Unit tests for measurement validation rules."""

from app.schemas.common import EntityType
from app.validation.engine import ValidationError, validate_entity
from app.validation.rules.measurement import validate_batch


def _valid_measurement() -> dict:
    return {
        "uid": "meas-001",
        "meter": "api_requests",
        "account": "acme_corp",
        "ts": "2024-01-15T10:30:00Z",
        "measure": {"requests": 150, "bytes": 2048.5},
    }


def _errors_for(entity_type: EntityType, data: dict) -> list[ValidationError]:
    return validate_entity(entity_type, data)


def _error_fields(errors: list[ValidationError]) -> list[str]:
    return [e.field for e in errors]


class TestMeasurementValidation:
    def test_valid_measurement_passes(self) -> None:
        errors = _errors_for(EntityType.measurement, _valid_measurement())
        assert errors == []

    def test_missing_uid(self) -> None:
        data = _valid_measurement()
        del data["uid"]
        errors = _errors_for(EntityType.measurement, data)
        assert "uid" in _error_fields(errors)

    def test_missing_meter(self) -> None:
        data = _valid_measurement()
        del data["meter"]
        errors = _errors_for(EntityType.measurement, data)
        assert "meter" in _error_fields(errors)

    def test_missing_account(self) -> None:
        data = _valid_measurement()
        del data["account"]
        errors = _errors_for(EntityType.measurement, data)
        assert "account" in _error_fields(errors)

    def test_missing_ts(self) -> None:
        data = _valid_measurement()
        del data["ts"]
        errors = _errors_for(EntityType.measurement, data)
        assert "ts" in _error_fields(errors)

    def test_invalid_ts_format(self) -> None:
        data = _valid_measurement()
        data["ts"] = "2024-01-15"
        errors = _errors_for(EntityType.measurement, data)
        assert "ts" in _error_fields(errors)

    def test_valid_ts_with_timezone_offset(self) -> None:
        data = _valid_measurement()
        data["ts"] = "2024-01-15T10:30:00+05:30"
        errors = _errors_for(EntityType.measurement, data)
        assert errors == []

    def test_missing_all_categories(self) -> None:
        data = {
            "uid": "meas-001",
            "meter": "api_requests",
            "account": "acme_corp",
            "ts": "2024-01-15T10:30:00Z",
        }
        errors = _errors_for(EntityType.measurement, data)
        assert "measure" in _error_fields(errors)

    def test_measure_not_dict(self) -> None:
        data = _valid_measurement()
        data["measure"] = [1, 2, 3]
        errors = _errors_for(EntityType.measurement, data)
        assert "measure" in _error_fields(errors)

    def test_measure_with_non_numeric_values(self) -> None:
        data = _valid_measurement()
        data["measure"] = {"requests": "not_a_number"}
        errors = _errors_for(EntityType.measurement, data)
        assert "measure.requests" in _error_fields(errors)

    def test_string_category_with_non_string_values(self) -> None:
        data = _valid_measurement()
        data["who"] = {"customer_id": 12345}
        errors = _errors_for(EntityType.measurement, data)
        assert "who.customer_id" in _error_fields(errors)

    def test_valid_with_multiple_categories(self) -> None:
        data = _valid_measurement()
        data["who"] = {"customer_id": "cust-123"}
        data["where"] = {"region": "us-east-1"}
        errors = _errors_for(EntityType.measurement, data)
        assert errors == []

    def test_valid_ets(self) -> None:
        data = _valid_measurement()
        data["ets"] = "2024-01-15T11:30:00Z"
        errors = _errors_for(EntityType.measurement, data)
        assert errors == []

    def test_invalid_ets_format(self) -> None:
        data = _valid_measurement()
        data["ets"] = "not-a-date"
        errors = _errors_for(EntityType.measurement, data)
        assert "ets" in _error_fields(errors)

    def test_valid_with_all_fields(self) -> None:
        data = _valid_measurement()
        data["ets"] = "2024-01-15T11:30:00Z"
        errors = _errors_for(EntityType.measurement, data)
        assert errors == []


class TestMeasurementBatchValidation:
    def test_valid_batch_passes(self) -> None:
        measurements = [_valid_measurement() for _ in range(5)]
        for i, m in enumerate(measurements):
            m["uid"] = f"meas-{i:03d}"
        errors = validate_batch(measurements)
        assert errors == []

    def test_batch_exceeds_limit(self) -> None:
        measurements = [{"uid": f"meas-{i}"} for i in range(1001)]
        errors = validate_batch(measurements)
        assert any("exceeds limit" in e.message for e in errors)

    def test_duplicate_uids(self) -> None:
        measurements = [
            {"uid": "meas-001", "meter": "m1", "account": "a1"},
            {"uid": "meas-001", "meter": "m2", "account": "a2"},
        ]
        errors = validate_batch(measurements)
        assert any("Duplicate uid" in e.message for e in errors)

    def test_empty_batch_passes(self) -> None:
        errors = validate_batch([])
        assert errors == []
