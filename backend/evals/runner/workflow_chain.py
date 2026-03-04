"""Chained workflow execution for evaluations.

Runs WF1 → WF2 → WF3 in sequence, feeding approved entities from each
workflow into the next. Each function compiles a fresh graph with MemorySaver
and runs it with auto-approve.
"""

from uuid import uuid4

from evals.runner.auto_approver import run_graph_with_auto_approve
from evals.runner.graph_harness import (
    build_wf1_state,
    build_wf2_state,
    build_wf3_state,
    compile_eval_graph,
    eval_patches,
)


def _make_config() -> dict:
    """Create a LangGraph config with a unique thread_id."""
    return {"configurable": {"thread_id": str(uuid4())}}


async def run_wf1(
    example,
    model_id: str,
    patches_fn=eval_patches,
) -> dict:
    """Run WF1 (product_meter_aggregation) and return final state."""
    graph = compile_eval_graph("product_meter_aggregation")
    initial = build_wf1_state(example, model_id)
    config = _make_config()
    with patches_fn(example):
        return await run_graph_with_auto_approve(graph, initial, config)


async def run_wf2(
    example,
    wf1_state: dict,
    model_id: str,
    patches_fn=eval_patches,
) -> dict:
    """Run WF2 (plan_pricing) and return final state."""
    graph = compile_eval_graph("plan_pricing")
    initial = build_wf2_state(example, wf1_state, model_id)
    config = _make_config()
    with patches_fn(example, wf1_state=wf1_state):
        return await run_graph_with_auto_approve(graph, initial, config)


async def run_wf3(
    example,
    wf1_state: dict,
    wf2_state: dict,
    model_id: str,
    patches_fn=eval_patches,
) -> dict:
    """Run WF3 (account_setup) and return final state."""
    graph = compile_eval_graph("account_setup")
    initial = build_wf3_state(example, wf1_state, wf2_state, model_id)
    config = _make_config()
    with patches_fn(example, wf1_state=wf1_state, wf2_state=wf2_state):
        return await run_graph_with_auto_approve(graph, initial, config)


async def run_full_chain(
    example,
    model_id: str,
    patches_fn=eval_patches,
) -> dict:
    """Run WF1 → WF2 → WF3 in sequence, returning all final states."""
    wf1 = await run_wf1(example, model_id, patches_fn)
    wf2 = await run_wf2(example, wf1, model_id, patches_fn)
    wf3 = await run_wf3(example, wf1, wf2, model_id, patches_fn)
    return {"wf1": wf1, "wf2": wf2, "wf3": wf3}
