"""Cross-entity referential integrity evaluator (weight: 10%)."""

from __future__ import annotations

import re

from evals.datasets.base import EvalResult

# Workflow type → entity state keys
WORKFLOW_ENTITY_KEYS: dict[str, list[str]] = {
    "product_meter_aggregation": ["products", "meters", "aggregations", "compound_aggregations"],
    "plan_pricing": ["plan_templates", "plans", "pricing"],
    "account_setup": ["accounts", "account_plans"],
}


def _collect_ids(entities: list[dict], field: str = "id") -> set[str]:
    """Collect all non-None values for a field from entity list."""
    return {e.get(field) for e in entities if isinstance(e, dict) and e.get(field)}


def _collect_codes(entities: list[dict]) -> set[str]:
    """Collect all non-None code values from entity list."""
    return _collect_ids(entities, "code")


def _extract_codes_from_formula(formula: str) -> set[str]:
    """Extract aggregation code references from a compound aggregation formula."""
    # Match word tokens that look like codes (lowercase, alphanumeric + underscore)
    return set(re.findall(r"\b([a-z][a-z0-9_]*)\b", formula))


def _check_wf1(state: dict) -> tuple[int, int, list[dict]]:
    """Check WF1 referential integrity.

    - aggregation.targetField → meter dataField code
    - compound_aggregation.calculation → valid aggregation codes
    """
    total_refs = 0
    valid_refs = 0
    issues: list[dict] = []

    # Collect meter data field codes
    meter_data_fields: set[str] = set()
    for meter in state.get("meters", []):
        if isinstance(meter, dict):
            for df in meter.get("dataFields", []):
                if isinstance(df, dict) and df.get("code"):
                    meter_data_fields.add(df["code"])
            for df in meter.get("derivedFields", []):
                if isinstance(df, dict) and df.get("code"):
                    meter_data_fields.add(df["code"])

    # Check aggregation.targetField → meter dataField
    for i, agg in enumerate(state.get("aggregations", [])):
        if not isinstance(agg, dict):
            continue
        target = agg.get("targetField")
        if target:
            total_refs += 1
            if target in meter_data_fields:
                valid_refs += 1
            else:
                issues.append(
                    {
                        "entity_type": "aggregation",
                        "index": i,
                        "name": agg.get("name", "unknown"),
                        "field": "targetField",
                        "value": target,
                        "issue": "targetField not found in any meter dataField",
                    }
                )

    # Check compound_aggregation.calculation → aggregation codes
    agg_codes = _collect_codes(state.get("aggregations", []))
    for i, comp_agg in enumerate(state.get("compound_aggregations", [])):
        if not isinstance(comp_agg, dict):
            continue
        calc = comp_agg.get("calculation", "")
        if calc:
            referenced_codes = _extract_codes_from_formula(calc)
            # Filter to only tokens that could be aggregation references
            # (exclude common operators/keywords)
            for code in referenced_codes:
                if code in agg_codes:
                    total_refs += 1
                    valid_refs += 1
                # Only count as a ref if it could plausibly be an agg code
                # (i.e., it's not a common math keyword)
                elif code not in {"min", "max", "abs", "if", "else", "and", "or", "not"}:
                    # Could be an agg code that's missing — but we can't be sure
                    # Only flag if no agg codes match at all
                    pass

            # Simpler approach: check that at least one agg code is referenced
            if agg_codes:
                total_refs += 1
                if referenced_codes & agg_codes:
                    valid_refs += 1
                else:
                    issues.append(
                        {
                            "entity_type": "compound_aggregation",
                            "index": i,
                            "name": comp_agg.get("name", "unknown"),
                            "field": "calculation",
                            "value": calc,
                            "issue": "calculation does not reference any known aggregation code",
                        }
                    )

    return total_refs, valid_refs, issues


def _check_wf2(state: dict) -> tuple[int, int, list[dict]]:
    """Check WF2 referential integrity.

    - planTemplate.productId → product
    - plan.planTemplateId → planTemplate
    - pricing.aggregationId or compoundAggregationId → valid aggregation
    """
    total_refs = 0
    valid_refs = 0
    issues: list[dict] = []

    product_ids = _collect_ids(state.get("approved_products", state.get("products", [])))
    plan_template_ids = _collect_ids(state.get("plan_templates", []))
    agg_ids = _collect_ids(state.get("approved_aggregations", state.get("aggregations", [])))
    compound_agg_ids = _collect_ids(
        state.get("approved_compound_aggregations", state.get("compound_aggregations", []))
    )

    # planTemplate.productId → product
    for i, pt in enumerate(state.get("plan_templates", [])):
        if not isinstance(pt, dict):
            continue
        pid = pt.get("productId")
        if pid:
            total_refs += 1
            if pid in product_ids:
                valid_refs += 1
            else:
                issues.append(
                    {
                        "entity_type": "plan_template",
                        "index": i,
                        "name": pt.get("name", "unknown"),
                        "field": "productId",
                        "value": pid,
                        "issue": "productId not found in products",
                    }
                )

    # plan.planTemplateId → planTemplate
    for i, plan in enumerate(state.get("plans", [])):
        if not isinstance(plan, dict):
            continue
        pt_id = plan.get("planTemplateId")
        if pt_id:
            total_refs += 1
            if pt_id in plan_template_ids:
                valid_refs += 1
            else:
                issues.append(
                    {
                        "entity_type": "plan",
                        "index": i,
                        "name": plan.get("name", "unknown"),
                        "field": "planTemplateId",
                        "value": pt_id,
                        "issue": "planTemplateId not found in plan_templates",
                    }
                )

    # pricing.aggregationId or compoundAggregationId → valid agg
    for i, p in enumerate(state.get("pricing", [])):
        if not isinstance(p, dict):
            continue
        agg_id = p.get("aggregationId")
        comp_agg_id = p.get("compoundAggregationId")
        if agg_id:
            total_refs += 1
            if agg_id in agg_ids:
                valid_refs += 1
            else:
                issues.append(
                    {
                        "entity_type": "pricing",
                        "index": i,
                        "name": p.get("code", f"pricing_{i}"),
                        "field": "aggregationId",
                        "value": agg_id,
                        "issue": "aggregationId not found in aggregations",
                    }
                )
        if comp_agg_id:
            total_refs += 1
            if comp_agg_id in compound_agg_ids:
                valid_refs += 1
            else:
                issues.append(
                    {
                        "entity_type": "pricing",
                        "index": i,
                        "name": p.get("code", f"pricing_{i}"),
                        "field": "compoundAggregationId",
                        "value": comp_agg_id,
                        "issue": "compoundAggregationId not found in compound_aggregations",
                    }
                )

    return total_refs, valid_refs, issues


def _check_wf3(state: dict) -> tuple[int, int, list[dict]]:
    """Check WF3 referential integrity.

    - accountPlan.accountId → account
    - accountPlan.planId → plan
    """
    total_refs = 0
    valid_refs = 0
    issues: list[dict] = []

    account_ids = _collect_ids(state.get("accounts", []))
    plan_ids = _collect_ids(state.get("approved_plans", state.get("plans", [])))

    for i, ap in enumerate(state.get("account_plans", [])):
        if not isinstance(ap, dict):
            continue

        acct_id = ap.get("accountId")
        if acct_id:
            total_refs += 1
            if acct_id in account_ids:
                valid_refs += 1
            else:
                issues.append(
                    {
                        "entity_type": "account_plan",
                        "index": i,
                        "name": ap.get("name", f"account_plan_{i}"),
                        "field": "accountId",
                        "value": acct_id,
                        "issue": "accountId not found in accounts",
                    }
                )

        plan_id = ap.get("planId")
        if plan_id:
            total_refs += 1
            if plan_id in plan_ids:
                valid_refs += 1
            else:
                issues.append(
                    {
                        "entity_type": "account_plan",
                        "index": i,
                        "name": ap.get("name", f"account_plan_{i}"),
                        "field": "planId",
                        "value": plan_id,
                        "issue": "planId not found in plans",
                    }
                )

    return total_refs, valid_refs, issues


_WF_CHECKERS = {
    "product_meter_aggregation": _check_wf1,
    "plan_pricing": _check_wf2,
    "account_setup": _check_wf3,
}


def evaluate(state: dict, reference: object, workflow_type: str) -> EvalResult:
    """Evaluate cross-entity referential integrity.

    Score = valid_references / total_references.
    """
    checker = _WF_CHECKERS.get(workflow_type)
    if not checker:
        return EvalResult(
            name="cross_entity",
            score=1.0,
            details=[],
            notes=f"No cross-entity checks for workflow type '{workflow_type}'",
        )

    total_refs, valid_refs, issues = checker(state)

    if total_refs == 0:
        score = 1.0
        notes = "No cross-entity references to validate"
    else:
        score = valid_refs / total_refs
        notes = f"{valid_refs}/{total_refs} cross-entity references valid"

    return EvalResult(name="cross_entity", score=score, details=issues, notes=notes)
