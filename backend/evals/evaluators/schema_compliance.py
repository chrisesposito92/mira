"""Schema compliance evaluator — reuses app validation engine (weight: 20%)."""

from app.schemas.common import EntityType
from app.validation.engine import validate_entity
from evals.datasets.base import EvalResult

# State key → EntityType mapping
STATE_KEY_TO_ENTITY_TYPE: dict[str, EntityType] = {
    "products": EntityType.product,
    "meters": EntityType.meter,
    "aggregations": EntityType.aggregation,
    "compound_aggregations": EntityType.compound_aggregation,
    "plan_templates": EntityType.plan_template,
    "plans": EntityType.plan,
    "pricing": EntityType.pricing,
    "accounts": EntityType.account,
    "account_plans": EntityType.account_plan,
}

# Workflow type → entity state keys
WORKFLOW_ENTITY_KEYS: dict[str, list[str]] = {
    "product_meter_aggregation": ["products", "meters", "aggregations", "compound_aggregations"],
    "plan_pricing": ["plan_templates", "plans", "pricing"],
    "account_setup": ["accounts", "account_plans"],
}


def evaluate(state: dict, reference: object, workflow_type: str) -> EvalResult:
    """Evaluate schema compliance using the app's validation engine.

    Score = entities_with_no_errors / total_entities.
    Warnings are reported but do not reduce score.
    """
    entity_keys = WORKFLOW_ENTITY_KEYS.get(workflow_type, [])
    total = 0
    no_errors = 0
    details: list[dict] = []

    for key in entity_keys:
        entity_type = STATE_KEY_TO_ENTITY_TYPE.get(key)
        if not entity_type:
            continue

        entities = state.get(key, [])
        for i, entity in enumerate(entities):
            if not isinstance(entity, dict):
                total += 1
                details.append(
                    {
                        "entity_type": key,
                        "index": i,
                        "errors": ["not a dict — cannot validate"],
                        "warnings": [],
                    }
                )
                continue

            total += 1
            validation_errors = validate_entity(entity_type, entity)
            errors = [e for e in validation_errors if e.severity == "error"]
            warnings = [e for e in validation_errors if e.severity == "warning"]

            if not errors:
                no_errors += 1

            if errors or warnings:
                details.append(
                    {
                        "entity_type": key,
                        "index": i,
                        "name": entity.get("name", entity.get("code", "unknown")),
                        "errors": [f"{e.field}: {e.message}" for e in errors],
                        "warnings": [f"{w.field}: {w.message}" for w in warnings],
                    }
                )

    score = no_errors / total if total > 0 else 1.0
    notes = f"{no_errors}/{total} entities pass schema validation (errors only)"

    return EvalResult(name="schema_compliance", score=score, details=details, notes=notes)
