"""WF3 (Account/AccountPlan) evaluation tests."""

import pytest

from evals.datasets.registry import ALL_EXAMPLES
from evals.evaluators.composite import compute_composite_score
from evals.evaluators.cross_entity import evaluate as eval_cross_entity
from evals.evaluators.schema_compliance import evaluate as eval_schema
from evals.evaluators.structural import evaluate as eval_structural
from evals.runner.auto_approver import run_graph_with_auto_approve
from evals.runner.graph_harness import (
    build_wf1_state,
    build_wf2_state,
    build_wf3_state,
    compile_eval_graph,
    eval_patches,
)

WF1_TYPE = "product_meter_aggregation"
WF2_TYPE = "plan_pricing"
WF3_TYPE = "account_setup"


def _run_all_evaluators(state: dict, reference) -> dict:
    from evals.evaluators.accuracy import evaluate as eval_accuracy
    from evals.evaluators.completeness import evaluate as eval_completeness

    return {
        "structural": eval_structural(state, reference, WF3_TYPE),
        "schema_compliance": eval_schema(state, reference, WF3_TYPE),
        "completeness": eval_completeness(state, reference, WF3_TYPE),
        "accuracy": eval_accuracy(state, reference, WF3_TYPE),
        "cross_entity": eval_cross_entity(state, reference, WF3_TYPE),
    }


@pytest.mark.eval
@pytest.mark.eval_live
@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=lambda e: e.name)
async def test_wf3_quality(example, eval_model_id):
    """WF3 generates valid accounts and account plans."""
    # Run WF1
    wf1_graph = compile_eval_graph(WF1_TYPE)
    wf1_state = build_wf1_state(example, eval_model_id)
    wf1_config = {"configurable": {"thread_id": f"eval-wf3-pre1-{example.name}"}}

    with eval_patches(example):
        wf1_result = await run_graph_with_auto_approve(wf1_graph, wf1_state, wf1_config)

    # Run WF2
    wf2_graph = compile_eval_graph(WF2_TYPE)
    wf2_state = build_wf2_state(example, wf1_result, eval_model_id)
    wf2_config = {"configurable": {"thread_id": f"eval-wf3-pre2-{example.name}"}}

    with eval_patches(example, wf1_state=wf1_result):
        wf2_result = await run_graph_with_auto_approve(wf2_graph, wf2_state, wf2_config)

    # Run WF3
    wf3_graph = compile_eval_graph(WF3_TYPE)
    wf3_state = build_wf3_state(example, wf1_result, wf2_result, eval_model_id)
    wf3_config = {"configurable": {"thread_id": f"eval-wf3-{example.name}"}}

    with eval_patches(example, wf1_state=wf1_result, wf2_state=wf2_result):
        wf3_result = await run_graph_with_auto_approve(wf3_graph, wf3_state, wf3_config)

    results = _run_all_evaluators(wf3_result, example.wf3_reference)
    composite = compute_composite_score(results, include_semantic=False)

    assert composite.score >= 0.50, (
        f"WF3 composite score too low: {composite.score:.2f}\nDetails: {composite.details}"
    )
