"""StateGraph for the usage submission workflow (Workflow 4).

Flow:
    load_approved_for_usage
    → generate_measurements → validate_entities → approve_entities (interrupt)
    → END

Requires a completed Workflow 3 (account_setup) for the same use case.
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.checkpointer import get_checkpointer
from app.agents.nodes.approval import approve_entities
from app.agents.nodes.load_approved_usage import load_approved_for_usage
from app.agents.nodes.measurement_gen import generate_measurements
from app.agents.nodes.validation import validate_entities
from app.agents.state import WorkflowState


def _build_graph() -> StateGraph:
    """Build the usage submission StateGraph (uncompiled)."""
    graph = StateGraph(WorkflowState)

    # Add nodes
    graph.add_node("load_approved_for_usage", load_approved_for_usage)
    graph.add_node("generate_measurements", generate_measurements)
    graph.add_node("validate_measurements", validate_entities)
    graph.add_node("approve_measurements", approve_entities)

    # Set entry point
    graph.set_entry_point("load_approved_for_usage")

    # Short-circuit to END if load fails (no approved entities)
    def route_after_load(state: WorkflowState) -> str:
        return END if state.get("current_step") == "error" else "generate_measurements"

    graph.add_conditional_edges("load_approved_for_usage", route_after_load)
    graph.add_edge("generate_measurements", "validate_measurements")
    graph.add_edge("validate_measurements", "approve_measurements")

    # End
    graph.add_edge("approve_measurements", END)

    return graph


_compiled_graph: CompiledStateGraph | None = None


async def build_usage_submission_graph() -> CompiledStateGraph:
    """Return the cached compiled graph, building it on first call."""
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph
    graph = _build_graph()
    checkpointer = await get_checkpointer()
    _compiled_graph = graph.compile(checkpointer=checkpointer)
    return _compiled_graph
