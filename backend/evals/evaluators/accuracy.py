"""Reference accuracy evaluator — fuzzy matching against reference entities (weight: 25%)."""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from scipy.optimize import linear_sum_assignment

from evals.datasets.base import EvalResult

if TYPE_CHECKING:
    from evals.datasets.base import ReferenceEntity, WorkflowReference

# Workflow type → entity state keys
WORKFLOW_ENTITY_KEYS: dict[str, list[str]] = {
    "product_meter_aggregation": ["products", "meters", "aggregations", "compound_aggregations"],
    "plan_pricing": ["plan_templates", "plans", "pricing"],
    "account_setup": ["accounts", "account_plans"],
}

# Fields that require exact matching
EXACT_MATCH_FIELDS = {"aggregationType", "category", "billFrequency", "rounding", "type"}

# Fields that are numeric (within 10% tolerance)
NUMERIC_FIELDS = {
    "standingCharge",
    "minimumSpend",
    "quantityPerUnit",
    "fixedPrice",
    "unitPrice",
    "lowerLimit",
}

# Fields that are counts (exact match)
COUNT_FIELDS = {"billFrequencyInterval", "daysBeforeBillDue", "precision"}

# Fields that are booleans (presence check)
BOOLEAN_FIELDS = {"cumulative", "bespoke", "tiersSpanPlan"}

# Weight breakdown for per-entity scoring
NAME_WEIGHT = 0.30
KEY_FIELD_WEIGHT = 0.50
STRUCTURE_WEIGHT = 0.20


def _name_similarity(generated: dict, ref: ReferenceEntity) -> float:
    """Score name similarity using SequenceMatcher."""
    gen_name = generated.get("name", "")
    ref_name = ref.name
    if not gen_name or not ref_name:
        return 0.0
    return difflib.SequenceMatcher(None, gen_name.lower(), ref_name.lower()).ratio()


def _field_match_score(gen_value: object, ref_value: object, field_name: str) -> float:
    """Score a single field match based on its type."""
    if gen_value is None or ref_value is None:
        return 0.0

    # Exact match fields
    if field_name in EXACT_MATCH_FIELDS:
        return 1.0 if str(gen_value) == str(ref_value) else 0.0

    # Numeric fields — within 10% tolerance
    if field_name in NUMERIC_FIELDS:
        try:
            gen_num = float(gen_value)
            ref_num = float(ref_value)
            if ref_num == 0:
                return 1.0 if gen_num == 0 else 0.0
            ratio = abs(gen_num - ref_num) / abs(ref_num)
            return 1.0 if ratio <= 0.1 else max(0.0, 1.0 - ratio)
        except (ValueError, TypeError):
            return 0.0

    # Count fields — exact match
    if field_name in COUNT_FIELDS:
        try:
            return 1.0 if int(gen_value) == int(ref_value) else 0.0
        except (ValueError, TypeError):
            return 0.0

    # Boolean fields — presence check
    if field_name in BOOLEAN_FIELDS:
        return 1.0 if bool(gen_value) == bool(ref_value) else 0.0

    # Default: fuzzy string matching (concept matching)
    gen_str = str(gen_value).lower()
    ref_str = str(ref_value).lower()
    return difflib.SequenceMatcher(None, gen_str, ref_str).ratio()


def _key_field_similarity(generated: dict, ref: ReferenceEntity) -> float:
    """Score key field matching across all reference key fields."""
    if not ref.key_fields:
        return 1.0

    scores: list[float] = []
    for field_name, ref_value in ref.key_fields.items():
        gen_value = generated.get(field_name)
        scores.append(_field_match_score(gen_value, ref_value, field_name))

    return sum(scores) / len(scores) if scores else 1.0


def _structure_similarity(generated: dict, ref: ReferenceEntity) -> float:
    """Score structural similarity based on field overlap."""
    if not ref.key_fields:
        return 1.0

    ref_fields = set(ref.key_fields.keys())
    gen_fields = set(generated.keys())

    if not ref_fields:
        return 1.0

    overlap = ref_fields & gen_fields
    return len(overlap) / len(ref_fields)


def _entity_score(generated: dict, ref: ReferenceEntity) -> float:
    """Compute weighted score for a single generated entity vs reference."""
    name_score = _name_similarity(generated, ref)
    field_score = _key_field_similarity(generated, ref)
    struct_score = _structure_similarity(generated, ref)

    return (
        NAME_WEIGHT * name_score + KEY_FIELD_WEIGHT * field_score + STRUCTURE_WEIGHT * struct_score
    )


def _match_entities(
    generated: list[dict],
    refs: list[ReferenceEntity],
) -> tuple[float, list[dict]]:
    """Use Hungarian algorithm for optimal 1:1 matching and return average score + details."""
    if not refs:
        return (1.0, [])
    if not generated:
        return (0.0, [{"issue": f"0 generated vs {len(refs)} expected"}])

    n_gen = len(generated)
    n_ref = len(refs)

    # Build cost matrix (negative scores for minimization)
    cost_matrix: list[list[float]] = []
    for i in range(n_gen):
        row: list[float] = []
        for j in range(n_ref):
            row.append(-_entity_score(generated[i], refs[j]))
        cost_matrix.append(row)

    # Hungarian algorithm
    row_indices, col_indices = linear_sum_assignment(cost_matrix)

    matched_scores: list[float] = []
    details: list[dict] = []

    for row_idx, col_idx in zip(row_indices, col_indices):
        score = -cost_matrix[row_idx][col_idx]
        matched_scores.append(score)
        details.append(
            {
                "generated_index": int(row_idx),
                "generated_name": generated[row_idx].get("name", "unnamed"),
                "reference_name": refs[col_idx].name,
                "score": round(score, 3),
                "name_sim": round(_name_similarity(generated[row_idx], refs[col_idx]), 3),
                "field_sim": round(_key_field_similarity(generated[row_idx], refs[col_idx]), 3),
                "struct_sim": round(_structure_similarity(generated[row_idx], refs[col_idx]), 3),
            }
        )

    # Unmatched references get score 0
    unmatched_refs = n_ref - len(matched_scores)
    for _ in range(unmatched_refs):
        matched_scores.append(0.0)

    avg_score = sum(matched_scores) / len(matched_scores) if matched_scores else 0.0
    return (avg_score, details)


def evaluate(state: dict, reference: WorkflowReference, workflow_type: str) -> EvalResult:
    """Evaluate accuracy via fuzzy matching against reference entities.

    Uses Hungarian algorithm for optimal 1:1 matching.
    Per-entity score = 0.30 * name_sim + 0.50 * key_field_sim + 0.20 * structure_sim.
    """
    entity_keys = WORKFLOW_ENTITY_KEYS.get(workflow_type, [])
    type_scores: list[float] = []
    all_details: list[dict] = []

    for key in entity_keys:
        refs = reference.entities.get(key, [])
        if not refs:
            continue

        generated = state.get(key, [])
        type_score, match_details = _match_entities(generated, refs)
        type_scores.append(type_score)

        all_details.append(
            {
                "entity_type": key,
                "score": round(type_score, 3),
                "generated_count": len(generated),
                "reference_count": len(refs),
                "matches": match_details,
            }
        )

    score = sum(type_scores) / len(type_scores) if type_scores else 0.0
    notes = f"{len(type_scores)} entity types matched, overall accuracy: {score:.1%}"

    return EvalResult(name="accuracy", score=score, details=all_details, notes=notes)
