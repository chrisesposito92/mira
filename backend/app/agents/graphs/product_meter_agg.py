"""StateGraph for the product/meter/aggregation generation workflow.

Flow:
    analyze_use_case → [should_clarify?]
        → yes: generate_clarifications (interrupt) → generate_products
        → no: generate_products
    → validate_products → approve_products (interrupt)
    → generate_meters → validate_meters → approve_meters (interrupt)
    → generate_aggregations → validate_aggregations → approve_aggregations (interrupt)
    → END
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.checkpointer import get_checkpointer
from app.agents.nodes.analysis import analyze_use_case
from app.agents.nodes.approval import approve_entities
from app.agents.nodes.clarification import generate_clarifications
from app.agents.nodes.generation import (
    generate_aggregations,
    generate_meters,
    generate_products,
)
from app.agents.nodes.validation import validate_entities
from app.agents.state import WorkflowState


def _should_clarify(state: WorkflowState) -> str:
    """Conditional edge: route to clarification or skip to product generation."""
    if state.get("needs_clarification"):
        return "generate_clarifications"
    return "generate_products"


def _route_after_gen_products(state: WorkflowState) -> str:
    """Route to END if generation failed, otherwise proceed to validation."""
    return END if state.get("current_step") == "error" else "validate_products"


def _route_after_gen_meters(state: WorkflowState) -> str:
    """Route to END if generation failed, otherwise proceed to validation."""
    return END if state.get("current_step") == "error" else "validate_meters"


def _route_after_gen_aggregations(state: WorkflowState) -> str:
    """Route to END if generation failed, otherwise proceed to validation."""
    return END if state.get("current_step") == "error" else "validate_aggregations"


def _build_graph() -> StateGraph:
    """Build the product/meter/aggregation StateGraph (uncompiled)."""
    graph = StateGraph(WorkflowState)

    # Add nodes
    graph.add_node("analyze_use_case", analyze_use_case)
    graph.add_node("generate_clarifications", generate_clarifications)
    graph.add_node("generate_products", generate_products)
    graph.add_node("validate_products", validate_entities)
    graph.add_node("approve_products", approve_entities)
    graph.add_node("generate_meters", generate_meters)
    graph.add_node("validate_meters", validate_entities)
    graph.add_node("approve_meters", approve_entities)
    graph.add_node("generate_aggregations", generate_aggregations)
    graph.add_node("validate_aggregations", validate_entities)
    graph.add_node("approve_aggregations", approve_entities)

    # Set entry point
    graph.set_entry_point("analyze_use_case")

    # Conditional edge: clarify or go straight to product generation
    graph.add_conditional_edges(
        "analyze_use_case",
        _should_clarify,
        {
            "generate_clarifications": "generate_clarifications",
            "generate_products": "generate_products",
        },
    )

    # After clarification, proceed to product generation
    graph.add_edge("generate_clarifications", "generate_products")

    # Product pipeline: generate → [error?] → validate → approve
    graph.add_conditional_edges("generate_products", _route_after_gen_products)
    graph.add_edge("validate_products", "approve_products")

    # Meter pipeline: generate → [error?] → validate → approve
    graph.add_edge("approve_products", "generate_meters")
    graph.add_conditional_edges("generate_meters", _route_after_gen_meters)
    graph.add_edge("validate_meters", "approve_meters")

    # Aggregation pipeline: generate → [error?] → validate → approve
    graph.add_edge("approve_meters", "generate_aggregations")
    graph.add_conditional_edges("generate_aggregations", _route_after_gen_aggregations)
    graph.add_edge("validate_aggregations", "approve_aggregations")

    # End
    graph.add_edge("approve_aggregations", END)

    return graph


_compiled_graph = None


async def build_product_meter_agg_graph() -> CompiledStateGraph:
    """Return the cached compiled graph, building it on first call."""
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph
    graph = _build_graph()
    checkpointer = await get_checkpointer()
    _compiled_graph = graph.compile(checkpointer=checkpointer)
    return _compiled_graph
