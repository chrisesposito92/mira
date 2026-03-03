"""Full WF1→WF2→WF3 chain evaluation tests."""

import pytest

from evals.datasets.registry import ALL_EXAMPLES
from evals.evaluators.composite import compute_composite_score
from evals.evaluators.cross_entity import evaluate as eval_cross_entity
from evals.evaluators.schema_compliance import evaluate as eval_schema
from evals.evaluators.structural import evaluate as eval_structural
from evals.runner.graph_harness import eval_patches
from evals.runner.workflow_chain import run_full_chain


def _run_evaluators(state: dict, reference, wf_type: str) -> dict:
    from evals.evaluators.accuracy import evaluate as eval_accuracy
    from evals.evaluators.completeness import evaluate as eval_completeness

    return {
        "structural": eval_structural(state, reference, wf_type),
        "schema_compliance": eval_schema(state, reference, wf_type),
        "completeness": eval_completeness(state, reference, wf_type),
        "accuracy": eval_accuracy(state, reference, wf_type),
        "cross_entity": eval_cross_entity(state, reference, wf_type),
    }


@pytest.mark.eval
@pytest.mark.eval_live
@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=lambda e: e.name)
async def test_full_chain(example, eval_model_id):
    """Full WF1→WF2→WF3 chain produces valid configurations."""
    chain_result = await run_full_chain(example, eval_model_id, eval_patches)

    # Evaluate each workflow
    wf1_results = _run_evaluators(
        chain_result["wf1"], example.wf1_reference, "product_meter_aggregation"
    )
    wf2_results = _run_evaluators(chain_result["wf2"], example.wf2_reference, "plan_pricing")
    wf3_results = _run_evaluators(chain_result["wf3"], example.wf3_reference, "account_setup")

    wf1_score = compute_composite_score(wf1_results, include_semantic=False)
    wf2_score = compute_composite_score(wf2_results, include_semantic=False)
    wf3_score = compute_composite_score(wf3_results, include_semantic=False)

    chain_avg = (wf1_score.score + wf2_score.score + wf3_score.score) / 3.0

    assert chain_avg >= 0.50, (
        f"Chain average score too low: {chain_avg:.2f} "
        f"(WF1={wf1_score.score:.2f}, WF2={wf2_score.score:.2f}, WF3={wf3_score.score:.2f})"
    )
