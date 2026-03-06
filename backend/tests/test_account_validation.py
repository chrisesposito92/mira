"""Unit tests for account and account_plan validation rules."""

from app.schemas.common import EntityType
from app.validation.engine import ValidationError, validate_entity


def _valid_account() -> dict:
    return {
        "name": "Acme Corp",
        "code": "acme_corp",
        "emailAddress": "billing@acme.com",
    }


def _valid_account_plan() -> dict:
    return {
        "accountId": "acc-123",
        "planId": "plan-456",
        "startDate": "2024-01-01",
    }


def _errors_for(entity_type: EntityType, data: dict) -> list[ValidationError]:
    return validate_entity(entity_type, data)


def _error_fields(errors: list[ValidationError]) -> list[str]:
    return [e.field for e in errors]


class TestAccountValidation:
    def test_valid_account_passes(self) -> None:
        errors = _errors_for(EntityType.account, _valid_account())
        assert errors == []

    def test_missing_name(self) -> None:
        data = _valid_account()
        del data["name"]
        errors = _errors_for(EntityType.account, data)
        assert "name" in _error_fields(errors)

    def test_missing_code(self) -> None:
        data = _valid_account()
        del data["code"]
        errors = _errors_for(EntityType.account, data)
        assert "code" in _error_fields(errors)

    def test_missing_email(self) -> None:
        data = _valid_account()
        del data["emailAddress"]
        errors = _errors_for(EntityType.account, data)
        assert "emailAddress" in _error_fields(errors)

    def test_invalid_email_format(self) -> None:
        data = _valid_account()
        data["emailAddress"] = "not-an-email"
        errors = _errors_for(EntityType.account, data)
        assert "emailAddress" in _error_fields(errors)

    def test_invalid_currency_lowercase(self) -> None:
        data = _valid_account()
        data["currency"] = "usd"
        errors = _errors_for(EntityType.account, data)
        assert "currency" in _error_fields(errors)

    def test_invalid_currency_wrong_length(self) -> None:
        data = _valid_account()
        data["currency"] = "US"
        errors = _errors_for(EntityType.account, data)
        assert "currency" in _error_fields(errors)

    def test_valid_currency(self) -> None:
        data = _valid_account()
        data["currency"] = "USD"
        errors = _errors_for(EntityType.account, data)
        assert errors == []

    def test_address_not_dict(self) -> None:
        data = _valid_account()
        data["address"] = "123 Main St"
        errors = _errors_for(EntityType.account, data)
        assert "address" in _error_fields(errors)

    def test_valid_address(self) -> None:
        data = _valid_account()
        data["address"] = {"addressLine1": "123 Main St", "locality": "NYC"}
        errors = _errors_for(EntityType.account, data)
        assert errors == []

    def test_negative_days_before_bill_due(self) -> None:
        data = _valid_account()
        data["daysBeforeBillDue"] = -1
        errors = _errors_for(EntityType.account, data)
        assert "daysBeforeBillDue" in _error_fields(errors)

    def test_valid_days_before_bill_due(self) -> None:
        data = _valid_account()
        data["daysBeforeBillDue"] = 30
        errors = _errors_for(EntityType.account, data)
        assert errors == []

    def test_custom_fields_not_dict(self) -> None:
        data = _valid_account()
        data["customFields"] = "not a dict"
        errors = _errors_for(EntityType.account, data)
        assert "customFields" in _error_fields(errors)

    def test_valid_with_all_optional_fields(self) -> None:
        data = _valid_account()
        data["currency"] = "EUR"
        data["address"] = {"addressLine1": "1 Rue de Paris", "locality": "Paris"}
        data["daysBeforeBillDue"] = 15
        data["customFields"] = {"tier": "enterprise"}
        errors = _errors_for(EntityType.account, data)
        assert errors == []


class TestAccountPlanValidation:
    def test_valid_account_plan_passes(self) -> None:
        errors = _errors_for(EntityType.account_plan, _valid_account_plan())
        assert errors == []

    def test_missing_account_id(self) -> None:
        data = _valid_account_plan()
        del data["accountId"]
        errors = _errors_for(EntityType.account_plan, data)
        assert "accountId" in _error_fields(errors)

    def test_missing_plan_id(self) -> None:
        data = _valid_account_plan()
        del data["planId"]
        errors = _errors_for(EntityType.account_plan, data)
        assert "planId" in _error_fields(errors)

    def test_missing_start_date(self) -> None:
        data = _valid_account_plan()
        del data["startDate"]
        errors = _errors_for(EntityType.account_plan, data)
        assert "startDate" in _error_fields(errors)

    def test_end_date_not_string(self) -> None:
        data = _valid_account_plan()
        data["endDate"] = 12345
        errors = _errors_for(EntityType.account_plan, data)
        assert "endDate" in _error_fields(errors)

    def test_valid_with_end_date(self) -> None:
        data = _valid_account_plan()
        data["endDate"] = "2024-12-31"
        errors = _errors_for(EntityType.account_plan, data)
        assert errors == []

    def test_custom_fields_not_dict(self) -> None:
        data = _valid_account_plan()
        data["customFields"] = [1, 2]
        errors = _errors_for(EntityType.account_plan, data)
        assert "customFields" in _error_fields(errors)

    def test_valid_with_custom_fields(self) -> None:
        data = _valid_account_plan()
        data["customFields"] = {"note": "primary plan"}
        errors = _errors_for(EntityType.account_plan, data)
        assert errors == []
