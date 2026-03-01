"""StateGraph for the account setup workflow (Workflow 3).

Flow:
    load_approved_for_accounts
    → generate_accounts → validate_entities → approve_entities (interrupt)
    → generate_account_plans → validate_entities → approve_entities (interrupt)
    → END

Requires a completed Workflow 2 (plan_pricing) for the same use case.
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.checkpointer import get_checkpointer
from app.agents.nodes.account_gen import generate_accounts
from app.agents.nodes.account_plan_gen import generate_account_plans
from app.agents.nodes.approval import approve_entities
from app.agents.nodes.load_approved_accounts import load_approved_for_accounts
from app.agents.nodes.validation import validate_entities
from app.agents.state import WorkflowState


def _build_graph() -> StateGraph:
    """Build the account setup StateGraph (uncompiled)."""
    graph = StateGraph(WorkflowState)

    # Add nodes
    graph.add_node("load_approved_for_accounts", load_approved_for_accounts)
    graph.add_node("generate_accounts", generate_accounts)
    graph.add_node("validate_accounts", validate_entities)
    graph.add_node("approve_accounts", approve_entities)
    graph.add_node("generate_account_plans", generate_account_plans)
    graph.add_node("validate_account_plans", validate_entities)
    graph.add_node("approve_account_plans", approve_entities)

    # Set entry point
    graph.set_entry_point("load_approved_for_accounts")

    # Short-circuit to END if load fails (no approved entities)
    def route_after_load(state: WorkflowState) -> str:
        return END if state.get("current_step") == "error" else "generate_accounts"

    graph.add_conditional_edges("load_approved_for_accounts", route_after_load)
    graph.add_edge("generate_accounts", "validate_accounts")
    graph.add_edge("validate_accounts", "approve_accounts")

    # AccountPlan pipeline: generate → validate → approve
    graph.add_edge("approve_accounts", "generate_account_plans")
    graph.add_edge("generate_account_plans", "validate_account_plans")
    graph.add_edge("validate_account_plans", "approve_account_plans")

    # End
    graph.add_edge("approve_account_plans", END)

    return graph


_compiled_graph: CompiledStateGraph | None = None


async def build_account_setup_graph() -> CompiledStateGraph:
    """Return the cached compiled graph, building it on first call."""
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph
    graph = _build_graph()
    checkpointer = await get_checkpointer()
    _compiled_graph = graph.compile(checkpointer=checkpointer)
    return _compiled_graph
