"""Shared utilities for LangGraph agent workflows."""

from typing import Any


def build_use_case_description(use_case: dict) -> str:
    """Build a description from use case data for prompt context."""
    title = use_case.get("title", "")
    description = use_case.get("description", "")
    industry = use_case.get("industry", "")
    parts = []
    if title:
        parts.append(f"Title: {title}")
    if description:
        parts.append(f"Description: {description}")
    if industry:
        parts.append(f"Industry: {industry}")
    return "\n".join(parts) if parts else "No use case details available."


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
