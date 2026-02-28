"""Shared utilities for LangGraph agent workflows."""

from typing import Any


def extract_interrupt_payload(graph_state: Any) -> dict | None:
    """Extract the interrupt payload from a LangGraph state snapshot.

    Returns the first interrupt value found, or None if no interrupts are pending.
    """
    if not graph_state.tasks:
        return None
    for task in graph_state.tasks:
        if hasattr(task, "interrupts") and task.interrupts:
            return task.interrupts[0].value
    return None
