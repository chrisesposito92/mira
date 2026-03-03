"""Weighted composite scorer — combines all evaluator results."""

from __future__ import annotations

from evals.datasets.base import EvalResult

WEIGHTS: dict[str, float] = {
    "structural": 0.10,
    "schema_compliance": 0.20,
    "completeness": 0.15,
    "accuracy": 0.25,
    "cross_entity": 0.10,
    "semantic": 0.20,
}


def compute_composite_score(
    results: dict[str, EvalResult],
    include_semantic: bool = True,
) -> EvalResult:
    """Compute weighted composite score from individual evaluator results.

    When semantic eval is skipped, remaining weights are redistributed proportionally.
    """
    active_weights = dict(WEIGHTS)

    if not include_semantic or "semantic" not in results:
        active_weights.pop("semantic", None)

    # Redistribute weights proportionally
    weight_sum = sum(active_weights.values())
    if weight_sum > 0:
        normalized_weights = {k: v / weight_sum for k, v in active_weights.items()}
    else:
        normalized_weights = {}

    # Compute weighted score
    weighted_score = 0.0
    breakdown: list[dict] = []

    for name, weight in normalized_weights.items():
        result = results.get(name)
        if result is None:
            continue
        contribution = weight * result.score
        weighted_score += contribution
        breakdown.append(
            {
                "evaluator": name,
                "score": round(result.score, 3),
                "weight": round(weight, 3),
                "contribution": round(contribution, 3),
                "notes": result.notes,
            }
        )

    # Format report
    report_lines = [
        "=== Composite Evaluation Report ===",
        f"Overall Score: {weighted_score:.1%}",
        "",
        "Breakdown:",
    ]
    for item in breakdown:
        report_lines.append(
            f"  {item['evaluator']:20s} "
            f"score={item['score']:.3f} x weight={item['weight']:.3f} "
            f"= {item['contribution']:.3f}"
        )
    report_lines.append("")
    report_lines.append(
        f"Semantic eval: {'included' if include_semantic and 'semantic' in results else 'skipped'}"
    )

    notes = "\n".join(report_lines)

    return EvalResult(
        name="composite",
        score=weighted_score,
        details=breakdown,
        notes=notes,
    )
