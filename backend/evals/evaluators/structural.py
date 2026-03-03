"""Structural validity evaluator — checks basic entity structure (weight: 10%)."""

import re

from evals.datasets.base import EvalResult

CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

# Entity types that require name+code fields
_REQUIRES_NAME = {
    "products",
    "meters",
    "aggregations",
    "compound_aggregations",
    "plan_templates",
    "plans",
    "accounts",
}
_REQUIRES_CODE = {
    "products",
    "meters",
    "aggregations",
    "compound_aggregations",
    "plan_templates",
    "plans",
    "accounts",
}

# Workflow type → entity state keys
WORKFLOW_ENTITY_KEYS: dict[str, list[str]] = {
    "product_meter_aggregation": ["products", "meters", "aggregations", "compound_aggregations"],
    "plan_pricing": ["plan_templates", "plans", "pricing"],
    "account_setup": ["accounts", "account_plans"],
}


def _check_entity(entity: object, state_key: str) -> list[str]:
    """Check a single entity for structural issues. Returns list of issue strings."""
    issues: list[str] = []

    if not isinstance(entity, dict):
        issues.append("not a dict")
        return issues

    if state_key in _REQUIRES_NAME:
        name = entity.get("name")
        if not name or (isinstance(name, str) and not name.strip()):
            issues.append("missing or empty name")

    if state_key in _REQUIRES_CODE:
        code = entity.get("code")
        if not code:
            issues.append("missing code")
        elif isinstance(code, str) and not CODE_PATTERN.match(code):
            issues.append(f"code '{code}' does not match ^[a-z][a-z0-9_]*$")

    # Check for empty required fields (strings that are blank)
    for key, value in entity.items():
        if isinstance(value, str) and value == "" and key not in ("description",):
            issues.append(f"empty string field: {key}")

    return issues


def evaluate(state: dict, reference: object, workflow_type: str) -> EvalResult:
    """Evaluate structural validity of generated entities.

    Score = clean_entities / total_entities.
    """
    entity_keys = WORKFLOW_ENTITY_KEYS.get(workflow_type, [])
    total = 0
    clean = 0
    details: list[dict] = []

    for key in entity_keys:
        entities = state.get(key, [])
        for i, entity in enumerate(entities):
            total += 1
            issues = _check_entity(entity, key)
            if not issues:
                clean += 1
            else:
                details.append(
                    {
                        "entity_type": key,
                        "index": i,
                        "name": entity.get("name", "unknown")
                        if isinstance(entity, dict)
                        else "N/A",
                        "issues": issues,
                    }
                )

    score = clean / total if total > 0 else 1.0
    notes = f"{clean}/{total} entities structurally valid"

    return EvalResult(name="structural", score=score, details=details, notes=notes)
