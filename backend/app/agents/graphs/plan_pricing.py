"""StateGraph for the plan/pricing generation workflow (Workflow 2).

Flow:
    load_approved_entities
    → generate_plan_templates → validate_entities → approve_entities (interrupt)
    → generate_plans → validate_entities → approve_entities (interrupt)
    → generate_pricing → validate_entities → approve_entities (interrupt)
    → END

Requires a completed Workflow 1 (product_meter_aggregation) for the same use case.
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.checkpointer import get_checkpointer, get_store
from app.agents.nodes.approval import approve_entities
from app.agents.nodes.load_approved import load_approved_entities
from app.agents.nodes.plan_gen import generate_plans
from app.agents.nodes.plan_template_gen import generate_plan_templates
from app.agents.nodes.pricing_gen import generate_pricing
from app.agents.nodes.validation import validate_entities
from app.agents.state import WorkflowState


def route_after_load(state: WorkflowState) -> str:
    """Route to END if load failed, otherwise proceed to generation."""
    return END if state.get("current_step") == "error" else "generate_plan_templates"


def _route_after_gen_plan_templates(state: WorkflowState) -> str:
    """Route to END if generation failed, otherwise proceed to validation."""
    return END if state.get("current_step") == "error" else "validate_plan_templates"


def _route_after_gen_plans(state: WorkflowState) -> str:
    """Route to END if generation failed, otherwise proceed to validation."""
    return END if state.get("current_step") == "error" else "validate_plans"


def _route_after_gen_pricing(state: WorkflowState) -> str:
    """Route to END if generation failed, otherwise proceed to validation."""
    return END if state.get("current_step") == "error" else "validate_pricing"


def _build_graph() -> StateGraph:
    """Build the plan/pricing StateGraph (uncompiled)."""
    graph = StateGraph(WorkflowState)

    # Add nodes
    graph.add_node("load_approved_entities", load_approved_entities)
    graph.add_node("generate_plan_templates", generate_plan_templates)
    graph.add_node("validate_plan_templates", validate_entities)
    graph.add_node("approve_plan_templates", approve_entities)
    graph.add_node("generate_plans", generate_plans)
    graph.add_node("validate_plans", validate_entities)
    graph.add_node("approve_plans", approve_entities)
    graph.add_node("generate_pricing", generate_pricing)
    graph.add_node("validate_pricing", validate_entities)
    graph.add_node("approve_pricing", approve_entities)

    # Set entry point
    graph.set_entry_point("load_approved_entities")

    # Short-circuit to END if load fails (no approved entities)
    graph.add_conditional_edges("load_approved_entities", route_after_load)

    # PlanTemplate pipeline: generate → [error?] → validate → approve
    graph.add_conditional_edges("generate_plan_templates", _route_after_gen_plan_templates)
    graph.add_edge("validate_plan_templates", "approve_plan_templates")

    # Plan pipeline: generate → [error?] → validate → approve
    graph.add_edge("approve_plan_templates", "generate_plans")
    graph.add_conditional_edges("generate_plans", _route_after_gen_plans)
    graph.add_edge("validate_plans", "approve_plans")

    # Pricing pipeline: generate → [error?] → validate → approve
    graph.add_edge("approve_plans", "generate_pricing")
    graph.add_conditional_edges("generate_pricing", _route_after_gen_pricing)
    graph.add_edge("validate_pricing", "approve_pricing")

    # End
    graph.add_edge("approve_pricing", END)

    return graph


_compiled_graph: CompiledStateGraph | None = None


async def build_plan_pricing_graph() -> CompiledStateGraph:
    """Return the cached compiled graph, building it on first call."""
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph
    graph = _build_graph()
    checkpointer = await get_checkpointer()
    store = await get_store()
    _compiled_graph = graph.compile(checkpointer=checkpointer, store=store)
    return _compiled_graph
