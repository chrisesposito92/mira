"""StateGraph for the use case generator workflow.

Flow:
    research_customer -> [should_clarify?]
        -> yes: ask_clarification -> compile_use_cases -> END
        -> no: compile_use_cases -> END
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.nodes.use_case_clarify import ask_clarification
from app.agents.nodes.use_case_compile import compile_use_cases
from app.agents.nodes.use_case_research import research_customer
from app.agents.state import UseCaseGenState


def _should_clarify(state: UseCaseGenState) -> str:
    """Conditional edge: route to clarification or skip to compilation."""
    if state.get("needs_clarification"):
        return "ask_clarification"
    return "compile_use_cases"


def _build_graph() -> StateGraph:
    """Build the use case generator StateGraph (uncompiled)."""
    graph = StateGraph(UseCaseGenState)

    # Add nodes
    graph.add_node("research_customer", research_customer)
    graph.add_node("ask_clarification", ask_clarification)
    graph.add_node("compile_use_cases", compile_use_cases)

    # Set entry point
    graph.set_entry_point("research_customer")

    # Conditional edge: clarify or go straight to compilation
    graph.add_conditional_edges(
        "research_customer",
        _should_clarify,
        {
            "ask_clarification": "ask_clarification",
            "compile_use_cases": "compile_use_cases",
        },
    )

    # After clarification, proceed to compilation
    graph.add_edge("ask_clarification", "compile_use_cases")

    # End after compilation
    graph.add_edge("compile_use_cases", END)

    return graph


def build_use_case_gen_graph() -> CompiledStateGraph:
    """Build a compiled graph with a fresh per-session MemorySaver.

    Each session gets its own MemorySaver so checkpoint data is scoped
    to the session lifetime and garbage-collected when the session ends.
    """
    graph = _build_graph()
    return graph.compile(checkpointer=MemorySaver())
