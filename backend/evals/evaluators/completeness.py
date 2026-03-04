"""Completeness evaluator — compares entity counts vs reference (weight: 15%)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from evals.datasets.base import EvalResult

if TYPE_CHECKING:
    from evals.datasets.base import WorkflowReference

# Workflow type → entity state keys
WORKFLOW_ENTITY_KEYS: dict[str, list[str]] = {
    "product_meter_aggregation": ["products", "meters", "aggregations", "compound_aggregations"],
    "plan_pricing": ["plan_templates", "plans", "pricing"],
    "account_setup": ["accounts", "account_plans"],
}

OVER_GENERATION_THRESHOLD = 1.5
OVER_GENERATION_PENALTY = 0.9


def evaluate(state: dict, reference: WorkflowReference, workflow_type: str) -> EvalResult:
    """Evaluate completeness by comparing entity counts to expected counts.

    Score per type = min(generated, expected) / expected.
    0.9x penalty if generated > 150% of expected (over-generation).
    Overall = average across entity types.
    """
    entity_keys = WORKFLOW_ENTITY_KEYS.get(workflow_type, [])
    expected_counts = reference.expected_counts
    scores: list[float] = []
    details: list[dict] = []

    for key in entity_keys:
        expected = expected_counts.get(key, 0)
        if expected == 0:
            # If no entities expected for this type, skip it
            continue

        generated = len(state.get(key, []))
        type_score = min(generated, expected) / expected

        # Penalize over-generation
        if generated > expected * OVER_GENERATION_THRESHOLD:
            type_score *= OVER_GENERATION_PENALTY

        type_score = min(type_score, 1.0)
        scores.append(type_score)

        details.append(
            {
                "entity_type": key,
                "expected": expected,
                "generated": generated,
                "score": round(type_score, 3),
                "over_generated": generated > expected * OVER_GENERATION_THRESHOLD,
            }
        )

    score = sum(scores) / len(scores) if scores else 1.0
    notes = f"{len(scores)} entity types evaluated, overall completeness: {score:.1%}"

    return EvalResult(name="completeness", score=score, details=details, notes=notes)
