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

from app.agents.checkpointer import get_checkpointer, get_store
from app.agents.nodes.account_gen import generate_accounts
from app.agents.nodes.account_plan_gen import generate_account_plans
from app.agents.nodes.approval import approve_entities
from app.agents.nodes.load_approved_accounts import load_approved_for_accounts
from app.agents.nodes.validation import validate_entities
from app.agents.state import WorkflowState


def route_after_load(state: WorkflowState) -> str:
    """Route to END if load failed, otherwise proceed to generation."""
    return END if state.get("current_step") == "error" else "generate_accounts"


def _route_after_gen_accounts(state: WorkflowState) -> str:
    """Route to END if generation failed, otherwise proceed to validation."""
    return END if state.get("current_step") == "error" else "validate_accounts"


def route_after_approve_accounts(state: WorkflowState) -> str:
    """Route to END if all accounts were rejected, otherwise generate account plans."""
    return END if not state.get("accounts") else "generate_account_plans"


def _route_after_gen_account_plans(state: WorkflowState) -> str:
    """Route to END if generation failed, otherwise proceed to validation."""
    return END if state.get("current_step") == "error" else "validate_account_plans"


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
    graph.add_conditional_edges("load_approved_for_accounts", route_after_load)

    # Account pipeline: generate → [error?] → validate → approve
    graph.add_conditional_edges("generate_accounts", _route_after_gen_accounts)
    graph.add_edge("validate_accounts", "approve_accounts")

    # Short-circuit to END if all accounts were rejected
    graph.add_conditional_edges("approve_accounts", route_after_approve_accounts)

    # AccountPlan pipeline: generate → [error?] → validate → approve
    graph.add_conditional_edges("generate_account_plans", _route_after_gen_account_plans)
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
    store = await get_store()
    _compiled_graph = graph.compile(checkpointer=checkpointer, store=store)
    return _compiled_graph
