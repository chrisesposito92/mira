"""Shared utilities for LangGraph agent workflows."""

import json
import logging
import re
from typing import Any

from app.schemas.common import ObjectStatus, WorkflowStatus, WorkflowType

logger = logging.getLogger(__name__)


def extract_llm_text(content: Any) -> str:
    """Extract plain text from an LLM response content field.

    Handles both string responses (OpenAI/Gemini) and content-block lists
    (Anthropic Claude) where response.content is a list of
    ``[{'type': 'text', 'text': '...'}]`` dicts.

    Also strips markdown code fences (```json ... ```) that LLMs sometimes
    add even when told not to.
    """
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        text = "".join(parts)
    else:
        text = str(content)

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    text = text.strip()
    fence_match = re.match(r"^```(?:json)?\s*\n?(.*?)\n?\s*```$", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    return text


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


def parse_entity_list(content: str) -> list[dict]:
    """Parse LLM response into a list of entity dicts."""
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # LLM might wrap in an object like {"products": [...]}
            for value in parsed.values():
                if isinstance(value, list):
                    return value
            return [parsed]
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse LLM response as JSON: %s", content[:200])
    return []


def fetch_workflow_window(supabase: Any, use_case_id: str, workflow_type: WorkflowType) -> Any:
    """Fetch the latest completed workflow time window for entity scoping."""
    return (
        supabase.table("workflows")
        .select("started_at, completed_at")
        .eq("use_case_id", use_case_id)
        .eq("workflow_type", workflow_type)
        .eq("status", WorkflowStatus.completed)
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )


def fetch_approved_entities(
    supabase: Any,
    use_case_id: str,
    entity_types: list[str],
    wf_result: Any,
) -> Any:
    """Fetch approved entities scoped to a workflow's time window."""
    query = (
        supabase.table("generated_objects")
        .select("id, entity_type, data")
        .eq("use_case_id", use_case_id)
        .eq("status", ObjectStatus.approved)
    )
    if len(entity_types) == 1:
        query = query.eq("entity_type", entity_types[0])
    else:
        query = query.in_("entity_type", entity_types)
    if wf_result.data:
        wf = wf_result.data[0]
        query = query.gte("created_at", wf["started_at"])
        if wf.get("completed_at"):
            query = query.lte("created_at", wf["completed_at"])
    return query.execute()


def inject_entity_id(row: dict) -> dict:
    """Merge generated_objects.id into the entity data dict."""
    return {**row.get("data", {}), "id": row["id"]}


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
