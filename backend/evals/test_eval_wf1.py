"""WF1 (Product/Meter/Aggregation/CompoundAggregation) evaluation tests."""

import pytest

from evals.datasets.registry import ALL_EXAMPLES
from evals.evaluators.composite import compute_composite_score
from evals.evaluators.cross_entity import evaluate as eval_cross_entity
from evals.evaluators.schema_compliance import evaluate as eval_schema
from evals.evaluators.structural import evaluate as eval_structural
from evals.runner.auto_approver import run_graph_with_auto_approve
from evals.runner.graph_harness import build_wf1_state, compile_eval_graph, eval_patches

WF_TYPE = "product_meter_aggregation"


def _run_all_evaluators(state: dict, reference, include_semantic: bool = False) -> dict:
    """Run all non-async evaluators and return results dict."""
    from evals.evaluators.accuracy import evaluate as eval_accuracy
    from evals.evaluators.completeness import evaluate as eval_completeness

    results = {
        "structural": eval_structural(state, reference, WF_TYPE),
        "schema_compliance": eval_schema(state, reference, WF_TYPE),
        "completeness": eval_completeness(state, reference, WF_TYPE),
        "accuracy": eval_accuracy(state, reference, WF_TYPE),
        "cross_entity": eval_cross_entity(state, reference, WF_TYPE),
    }
    return results


@pytest.mark.eval
@pytest.mark.eval_live
@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=lambda e: e.name)
async def test_wf1_quality(example, eval_model_id):
    """WF1 generates valid, complete, accurate entities for the use case."""
    graph = compile_eval_graph(WF_TYPE)
    initial_state = build_wf1_state(example, eval_model_id)
    config = {"configurable": {"thread_id": f"eval-wf1-{example.name}-{eval_model_id}"}}

    with eval_patches(example):
        state = await run_graph_with_auto_approve(graph, initial_state, config)

    results = _run_all_evaluators(state, example.wf1_reference)
    composite = compute_composite_score(results, include_semantic=False)

    # Minimum quality bar
    assert composite.score >= 0.50, (
        f"WF1 composite score too low: {composite.score:.2f}\nDetails: {composite.details}"
    )
    assert results["structural"].score >= 0.80, (
        f"Structural validity below threshold: {results['structural'].score:.2f}"
    )
    assert results["schema_compliance"].score >= 0.70, (
        f"Schema compliance below threshold: {results['schema_compliance'].score:.2f}"
    )


@pytest.mark.eval
@pytest.mark.eval_live
@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=lambda e: e.name)
async def test_wf1_structural(example, eval_model_id):
    """WF1 output passes structural validation."""
    graph = compile_eval_graph(WF_TYPE)
    initial_state = build_wf1_state(example, eval_model_id)
    config = {"configurable": {"thread_id": f"eval-wf1-struct-{example.name}"}}

    with eval_patches(example):
        state = await run_graph_with_auto_approve(graph, initial_state, config)

    result = eval_structural(state, example.wf1_reference, WF_TYPE)
    assert result.score >= 0.80, f"Structural score: {result.score:.2f}"
