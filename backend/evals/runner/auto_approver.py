"""Auto-approver for HITL interrupt gates during evaluation runs.

Runs a compiled LangGraph graph to completion by automatically approving
all entity gates and selecting the first option for clarification questions.
"""

from langgraph.types import Command

from app.agents.utils import extract_interrupt_payload


async def run_graph_with_auto_approve(
    graph,
    initial_state: dict,
    config: dict,
    max_iterations: int = 20,
) -> dict:
    """Run a compiled graph, auto-approving all interrupt gates.

    Args:
        graph: Compiled LangGraph StateGraph.
        initial_state: Initial state dict for the graph.
        config: LangGraph config with thread_id etc.
        max_iterations: Safety limit on interrupt loops.

    Returns:
        Final state dict from the graph.

    Raises:
        RuntimeError: If the auto-approve loop exceeds max_iterations.
    """
    await graph.ainvoke(initial_state, config)

    for _ in range(max_iterations):
        snapshot = await graph.aget_state(config)
        payload = extract_interrupt_payload(snapshot)

        if not payload:
            return snapshot.values

        if payload.get("type") == "clarification":
            questions = payload.get("questions", [])
            decisions = [{"selected_option": 0} for _ in questions]
        else:
            # Entity approval — approve all
            entities = payload.get("entities", [])
            decisions = [{"index": i, "action": "approve"} for i in range(len(entities))]

        await graph.ainvoke(Command(resume=decisions), config)

    raise RuntimeError(f"Auto-approve loop exceeded {max_iterations} iterations")
