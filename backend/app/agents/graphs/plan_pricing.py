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

from app.agents.checkpointer import get_checkpointer
from app.agents.nodes.approval import approve_entities
from app.agents.nodes.load_approved import load_approved_entities
from app.agents.nodes.plan_gen import generate_plans
from app.agents.nodes.plan_template_gen import generate_plan_templates
from app.agents.nodes.pricing_gen import generate_pricing
from app.agents.nodes.validation import validate_entities
from app.agents.state import WorkflowState


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

    # PlanTemplate pipeline: load → generate → validate → approve
    graph.add_edge("load_approved_entities", "generate_plan_templates")
    graph.add_edge("generate_plan_templates", "validate_plan_templates")
    graph.add_edge("validate_plan_templates", "approve_plan_templates")

    # Plan pipeline: generate → validate → approve
    graph.add_edge("approve_plan_templates", "generate_plans")
    graph.add_edge("generate_plans", "validate_plans")
    graph.add_edge("validate_plans", "approve_plans")

    # Pricing pipeline: generate → validate → approve
    graph.add_edge("approve_plans", "generate_pricing")
    graph.add_edge("generate_pricing", "validate_pricing")
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
    _compiled_graph = graph.compile(checkpointer=checkpointer)
    return _compiled_graph
