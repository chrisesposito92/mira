"""Unit tests for cross-entity validation."""

from app.schemas.common import EntityType
from app.validation.cross_entity import validate_cross_entity


class TestAccountPlanCrossValidation:
    def test_valid_refs_pass(self) -> None:
        entities = [{"accountId": "acc-1", "planId": "plan-1", "startDate": "2024-01-01"}]
        context = {
            "accounts": [{"id": "acc-1", "name": "Acme"}],
            "approved_plans": [{"id": "plan-1", "name": "Standard"}],
        }
        errors = validate_cross_entity(EntityType.account_plan, entities, context)
        assert errors == []

    def test_invalid_account_id(self) -> None:
        entities = [{"accountId": "acc-999", "planId": "plan-1", "startDate": "2024-01-01"}]
        context = {
            "accounts": [{"id": "acc-1", "name": "Acme"}],
            "approved_plans": [{"id": "plan-1", "name": "Standard"}],
        }
        errors = validate_cross_entity(EntityType.account_plan, entities, context)
        assert len(errors) == 1
        assert any(e["field"] == "accountId" for e in errors[0]["errors"])

    def test_invalid_plan_id(self) -> None:
        entities = [{"accountId": "acc-1", "planId": "plan-999", "startDate": "2024-01-01"}]
        context = {
            "accounts": [{"id": "acc-1", "name": "Acme"}],
            "approved_plans": [{"id": "plan-1", "name": "Standard"}],
        }
        errors = validate_cross_entity(EntityType.account_plan, entities, context)
        assert len(errors) == 1
        assert any(e["field"] == "planId" for e in errors[0]["errors"])

    def test_both_invalid(self) -> None:
        entities = [{"accountId": "acc-999", "planId": "plan-999", "startDate": "2024-01-01"}]
        context = {
            "accounts": [{"id": "acc-1", "name": "Acme"}],
            "approved_plans": [{"id": "plan-1", "name": "Standard"}],
        }
        errors = validate_cross_entity(EntityType.account_plan, entities, context)
        assert len(errors) == 1
        error_fields = [e["field"] for e in errors[0]["errors"]]
        assert "accountId" in error_fields
        assert "planId" in error_fields

    def test_empty_context_passes(self) -> None:
        """With empty context, cross-validation cannot check refs so should pass."""
        entities = [{"accountId": "acc-1", "planId": "plan-1", "startDate": "2024-01-01"}]
        context: dict = {}
        errors = validate_cross_entity(EntityType.account_plan, entities, context)
        assert errors == []


class TestMeasurementCrossValidation:
    def test_valid_refs_pass(self) -> None:
        entities = [
            {
                "uid": "m-1",
                "meter": "api_requests",
                "account": "acme_corp",
                "ts": "2024-01-15T10:00:00Z",
                "data": {"requests": 100},
            }
        ]
        context = {
            "approved_meters": [
                {
                    "code": "api_requests",
                    "dataFields": [{"code": "requests", "category": "MEASURE"}],
                }
            ],
            "approved_accounts": [{"code": "acme_corp", "name": "Acme"}],
        }
        errors = validate_cross_entity(EntityType.measurement, entities, context)
        assert errors == []

    def test_invalid_meter_code(self) -> None:
        entities = [
            {
                "uid": "m-1",
                "meter": "nonexistent_meter",
                "account": "acme_corp",
                "ts": "2024-01-15T10:00:00Z",
                "data": {"requests": 100},
            }
        ]
        context = {
            "approved_meters": [{"code": "api_requests"}],
            "approved_accounts": [{"code": "acme_corp"}],
        }
        errors = validate_cross_entity(EntityType.measurement, entities, context)
        assert len(errors) == 1
        assert any(e["field"] == "meter" for e in errors[0]["errors"])

    def test_invalid_account_code(self) -> None:
        entities = [
            {
                "uid": "m-1",
                "meter": "api_requests",
                "account": "nonexistent_account",
                "ts": "2024-01-15T10:00:00Z",
                "data": {"requests": 100},
            }
        ]
        context = {
            "approved_meters": [{"code": "api_requests"}],
            "approved_accounts": [{"code": "acme_corp"}],
        }
        errors = validate_cross_entity(EntityType.measurement, entities, context)
        assert len(errors) == 1
        assert any(e["field"] == "account" for e in errors[0]["errors"])

    def test_data_keys_mismatch_warning(self) -> None:
        entities = [
            {
                "uid": "m-1",
                "meter": "api_requests",
                "account": "acme_corp",
                "ts": "2024-01-15T10:00:00Z",
                "data": {"unknown_field": 100},
            }
        ]
        context = {
            "approved_meters": [
                {
                    "code": "api_requests",
                    "dataFields": [{"code": "requests", "category": "MEASURE"}],
                }
            ],
            "approved_accounts": [{"code": "acme_corp"}],
        }
        errors = validate_cross_entity(EntityType.measurement, entities, context)
        assert len(errors) == 1
        assert errors[0]["errors"][0]["severity"] == "warning"

    def test_empty_entities_returns_empty(self) -> None:
        errors = validate_cross_entity(EntityType.measurement, [], {})
        assert errors == []

    def test_unsupported_entity_type_returns_empty(self) -> None:
        errors = validate_cross_entity(EntityType.product, [{"name": "test"}], {})
        assert errors == []
