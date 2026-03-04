"""Graph compilation and mocking harness for evaluation runs.

Provides:
- compile_eval_graph() — compiles a workflow graph with MemorySaver
- eval_patches() — context manager applying all needed mocks for isolated runs
- build_wf*_state() — state builders for each workflow type
"""

import contextlib
from typing import Any
from unittest.mock import patch

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

# ---------------------------------------------------------------------------
# Graph compilation
# ---------------------------------------------------------------------------


def compile_eval_graph(workflow_type: str) -> CompiledStateGraph:
    """Import and compile a workflow graph with an in-memory checkpointer.

    Args:
        workflow_type: One of "product_meter_aggregation", "plan_pricing", "account_setup".

    Returns:
        Compiled StateGraph ready for ainvoke().
    """
    if workflow_type == "product_meter_aggregation":
        from app.agents.graphs.product_meter_agg import _build_graph
    elif workflow_type == "plan_pricing":
        from app.agents.graphs.plan_pricing import _build_graph
    elif workflow_type == "account_setup":
        from app.agents.graphs.account_setup import _build_graph
    else:
        raise ValueError(f"Unknown workflow_type: {workflow_type}")

    graph = _build_graph()
    return graph.compile(checkpointer=MemorySaver())


# ---------------------------------------------------------------------------
# Mock Supabase (matches tests/conftest.py pattern)
# ---------------------------------------------------------------------------


class _MockPostgrestResponse:
    """Mimics the PostgREST response from Supabase SDK."""

    def __init__(self, data: list[dict] | None = None):
        self.data = data or []


class _MockPostgrestBuilder:
    """Chainable mock supporting .table().select().eq()...execute()."""

    def __init__(self, data: list[dict] | None = None) -> None:
        self._data = data or []

    def select(self, *_args: object, **_kwargs: object) -> "_MockPostgrestBuilder":
        return self

    def insert(self, _row: Any, **_kwargs: object) -> "_MockPostgrestBuilder":
        return self

    def upsert(self, _rows: Any, **_kwargs: object) -> "_MockPostgrestBuilder":
        return self

    def update(self, _values: Any, **_kwargs: object) -> "_MockPostgrestBuilder":
        return self

    def delete(self, **_kwargs: object) -> "_MockPostgrestBuilder":
        return self

    def eq(self, _column: str, _value: Any) -> "_MockPostgrestBuilder":
        return self

    def in_(self, _column: str, _values: list[str]) -> "_MockPostgrestBuilder":
        return self

    def order(self, _column: str, **_kwargs: object) -> "_MockPostgrestBuilder":
        return self

    def limit(self, _count: int) -> "_MockPostgrestBuilder":
        return self

    def execute(self) -> _MockPostgrestResponse:
        return _MockPostgrestResponse(self._data)


class _MockSupabase:
    """Mock Supabase client with per-table data configuration."""

    def __init__(self, table_data: dict[str, list[dict]] | None = None) -> None:
        self._table_data = table_data or {}

    def table(self, name: str) -> _MockPostgrestBuilder:
        data = self._table_data.get(name, [])
        return _MockPostgrestBuilder(data)


# ---------------------------------------------------------------------------
# Patch context manager
# ---------------------------------------------------------------------------


def _format_load_rows(entities: list[dict], entity_type: str) -> list[dict]:
    """Format entity dicts as rows matching the generated_objects table shape."""
    return [
        {
            "id": e.get("id", f"eval-{entity_type}-{i}"),
            "entity_type": entity_type,
            "data": e,
            "status": "approved",
        }
        for i, e in enumerate(entities)
    ]


def eval_patches(
    example: Any,
    wf1_state: dict | None = None,
    wf2_state: dict | None = None,
) -> contextlib.ExitStack:
    """Return an ExitStack context manager applying all needed mocks.

    Args:
        example: EvalExample with .use_case dict.
        wf1_state: Final state from WF1 (needed for WF2/WF3 load nodes).
        wf2_state: Final state from WF2 (needed for WF3 load node).

    Returns:
        contextlib.ExitStack that should be used as a context manager.
    """
    stack = contextlib.ExitStack()

    # --- Analysis node mocks ---
    use_case = getattr(example, "use_case", {})
    analysis_supabase = _MockSupabase({"use_cases": [use_case]})

    stack.enter_context(
        patch(
            "app.agents.nodes.analysis.get_supabase_client",
            return_value=analysis_supabase,
        )
    )

    async def _noop_rag(*_args: object, **_kwargs: object) -> str:
        return ""

    stack.enter_context(patch("app.agents.nodes.analysis.rag_retrieve", side_effect=_noop_rag))

    # --- Approval node mock (no-op DB writes) ---
    approval_supabase = _MockSupabase()
    stack.enter_context(
        patch(
            "app.agents.nodes.approval.get_supabase_client",
            return_value=approval_supabase,
        )
    )

    # --- Load approved entities mock (WF2) ---
    wf1_rows: list[dict] = []
    if wf1_state:
        for etype, key in [
            ("product", "products"),
            ("meter", "meters"),
            ("aggregation", "aggregations"),
            ("compound_aggregation", "compound_aggregations"),
        ]:
            wf1_rows.extend(_format_load_rows(wf1_state.get(key, []), etype))

    # Build the use_cases + generated_objects data for load_approved node
    load_supabase = _MockSupabase(
        {
            "generated_objects": wf1_rows,
            "use_cases": [use_case],
        }
    )
    stack.enter_context(
        patch(
            "app.agents.nodes.load_approved.get_supabase_client",
            return_value=load_supabase,
        )
    )
    stack.enter_context(patch("app.agents.nodes.load_approved.rag_retrieve", side_effect=_noop_rag))

    # --- Load approved for accounts mock (WF3) ---
    wf3_rows = list(wf1_rows)  # WF1 entities
    if wf2_state:
        for etype, key in [
            ("plan_template", "plan_templates"),
            ("plan", "plans"),
            ("pricing", "pricing"),
        ]:
            wf3_rows.extend(_format_load_rows(wf2_state.get(key, []), etype))

    load_accounts_supabase = _MockSupabase(
        {
            "generated_objects": wf3_rows,
            "use_cases": [use_case],
        }
    )
    stack.enter_context(
        patch(
            "app.agents.nodes.load_approved_accounts.get_supabase_client",
            return_value=load_accounts_supabase,
        )
    )
    stack.enter_context(
        patch(
            "app.agents.nodes.load_approved_accounts.rag_retrieve",
            side_effect=_noop_rag,
        )
    )

    # --- Memory mock (no store) ---
    # Patch at the source module and at all import sites that bind the name at
    # module level (top-level imports resolve once, so we must patch each).
    for mem_target in [
        "app.agents.memory.get_store_from_config",
        "app.agents.nodes.approval.get_store_from_config",
    ]:
        stack.enter_context(patch(mem_target, return_value=None))

    return stack


# ---------------------------------------------------------------------------
# State builders
# ---------------------------------------------------------------------------


def build_wf1_state(example: Any, model_id: str) -> dict:
    """Build initial state for WF1 (product_meter_aggregation)."""
    return {
        "use_case_id": example.use_case.get("id", "eval-uc-1"),
        "project_id": example.use_case.get("project_id", "eval-project-1"),
        "model_id": model_id,
        "user_id": "eval-user",
        "messages": [],
        "current_step": "",
    }


def build_wf2_state(example: Any, wf1_results: dict, model_id: str) -> dict:
    """Build initial state for WF2 (plan_pricing).

    Carries forward approved entity lists from WF1 results.
    """
    return {
        "use_case_id": example.use_case.get("id", "eval-uc-1"),
        "project_id": example.use_case.get("project_id", "eval-project-1"),
        "model_id": model_id,
        "user_id": "eval-user",
        "approved_products": wf1_results.get("products", []),
        "approved_meters": wf1_results.get("meters", []),
        "approved_aggregations": wf1_results.get("aggregations", []),
        "approved_compound_aggregations": wf1_results.get("compound_aggregations", []),
        "messages": [],
        "current_step": "",
    }


def build_wf3_state(
    example: Any,
    wf1_results: dict,
    wf2_results: dict,
    model_id: str,
) -> dict:
    """Build initial state for WF3 (account_setup).

    Carries forward approved entity lists from WF1 + WF2 results.
    """
    return {
        "use_case_id": example.use_case.get("id", "eval-uc-1"),
        "project_id": example.use_case.get("project_id", "eval-project-1"),
        "model_id": model_id,
        "user_id": "eval-user",
        "approved_products": wf1_results.get("products", []),
        "approved_meters": wf1_results.get("meters", []),
        "approved_aggregations": wf1_results.get("aggregations", []),
        "approved_plan_templates": wf2_results.get("plan_templates", []),
        "approved_plans": wf2_results.get("plans", []),
        "approved_pricing": wf2_results.get("pricing", []),
        "messages": [],
        "current_step": "",
    }
