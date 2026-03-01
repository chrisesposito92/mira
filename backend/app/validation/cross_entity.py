"""Cross-entity validation — referential integrity checks across entity types."""

from dataclasses import asdict

from app.schemas.common import EntityType
from app.validation.engine import ValidationError


def validate_cross_entity(
    entity_type: EntityType,
    entities: list[dict],
    context: dict,
) -> list[dict]:
    """Validate cross-entity references for a batch of entities.

    Args:
        entity_type: The type of entities being validated.
        entities: List of entity dicts to validate.
        context: Dict of approved entity lists keyed by state field name
                 (e.g., {"approved_accounts": [...], "approved_plans": [...]}).

    Returns:
        List of error dicts in the same format as validation node errors:
        [{"entity_index": i, "entity_name": "...", "errors": [...]}]
    """
    if entity_type == EntityType.account_plan:
        return _validate_account_plan_refs(entities, context)
    if entity_type == EntityType.measurement:
        return _validate_measurement_refs(entities, context)
    return []


def _validate_account_plan_refs(entities: list[dict], context: dict) -> list[dict]:
    """Validate AccountPlan references to accounts and plans."""
    approved_accounts = context.get("accounts", [])
    approved_plans = context.get("approved_plans", [])

    account_ids = {a.get("id") for a in approved_accounts if a.get("id")}
    plan_ids = {p.get("id") for p in approved_plans if p.get("id")}

    all_errors: list[dict] = []
    for i, entity in enumerate(entities):
        errors: list[ValidationError] = []

        account_id = entity.get("accountId")
        if account_id and account_ids and account_id not in account_ids:
            errors.append(
                ValidationError(
                    field="accountId",
                    message=f"accountId '{account_id}' does not match any approved account",
                    severity="error",
                )
            )

        plan_id = entity.get("planId")
        if plan_id and plan_ids and plan_id not in plan_ids:
            errors.append(
                ValidationError(
                    field="planId",
                    message=f"planId '{plan_id}' does not match any approved plan",
                    severity="error",
                )
            )

        if errors:
            entity_name = entity.get("name", "") or f"AccountPlan: {str(account_id or '')[:8]}"
            all_errors.append(
                {
                    "entity_index": i,
                    "entity_name": entity_name,
                    "errors": [asdict(e) for e in errors],
                }
            )

    return all_errors


def _validate_measurement_refs(entities: list[dict], context: dict) -> list[dict]:
    """Validate Measurement references to meters and accounts."""
    approved_meters = context.get("approved_meters", [])
    approved_accounts = context.get("approved_accounts", [])

    meter_codes = {m.get("code") for m in approved_meters if m.get("code")}
    account_codes = {a.get("code") for a in approved_accounts if a.get("code")}

    # Collect meter data field codes for data key validation
    meter_data_fields: dict[str, set[str]] = {}
    for m in approved_meters:
        code = m.get("code")
        if code and m.get("dataFields"):
            meter_data_fields[code] = {df.get("code") for df in m["dataFields"] if df.get("code")}

    all_errors: list[dict] = []
    for i, entity in enumerate(entities):
        errors: list[ValidationError] = []

        meter_code = entity.get("meter")
        if meter_code and meter_codes and meter_code not in meter_codes:
            errors.append(
                ValidationError(
                    field="meter",
                    message=f"meter code '{meter_code}' does not match any approved meter",
                    severity="error",
                )
            )

        account_code = entity.get("account")
        if account_code and account_codes and account_code not in account_codes:
            errors.append(
                ValidationError(
                    field="account",
                    message=(f"account code '{account_code}' does not match any approved account"),
                    severity="error",
                )
            )

        # Data field key validation (warning only)
        data = entity.get("data", {})
        if meter_code and meter_code in meter_data_fields and isinstance(data, dict):
            expected_fields = meter_data_fields[meter_code]
            for key in data:
                if key not in expected_fields:
                    errors.append(
                        ValidationError(
                            field=f"data.{key}",
                            message=(
                                f"data key '{key}' not found in meter '{meter_code}' dataFields"
                            ),
                            severity="warning",
                        )
                    )

        if errors:
            entity_name = entity.get("uid", f"Measurement {i}")
            all_errors.append(
                {
                    "entity_index": i,
                    "entity_name": entity_name,
                    "errors": [asdict(e) for e in errors],
                }
            )

    return all_errors
