"""Shared utilities for LangGraph agent workflows."""

import json
import logging
import re
from typing import Any

from app.schemas.common import ObjectStatus

logger = logging.getLogger(__name__)


def _extract_json_block(text: str) -> str | None:
    """Find the first JSON array or object in *text* and validate it.

    Scans for the first ``[`` or ``{``, then finds the **last** matching
    ``]`` or ``}`` respectively.  If the extracted substring is valid JSON
    it is returned; otherwise ``None``.
    """
    open_chars = {"[": "]", "{": "}"}
    first_idx: int | None = None
    close_char: str | None = None
    for i, ch in enumerate(text):
        if ch in open_chars:
            first_idx = i
            close_char = open_chars[ch]
            break
    if first_idx is None or close_char is None:
        return None
    last_idx = text.rfind(close_char)
    if last_idx <= first_idx:
        return None
    candidate = text[first_idx : last_idx + 1]
    try:
        json.loads(candidate)
        return candidate
    except (json.JSONDecodeError, ValueError):
        return None


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

    # If text still isn't valid JSON, attempt to extract a JSON block
    try:
        json.loads(text)
    except (json.JSONDecodeError, ValueError):
        extracted = _extract_json_block(text)
        if extracted is not None:
            text = extracted

    return text


def build_use_case_description(use_case: dict) -> str:
    """Build a description from use case data for prompt context."""
    title = use_case.get("title", "")
    description = use_case.get("description", "")
    parts = []
    if title:
        parts.append(f"Title: {title}")
    if description:
        parts.append(f"Description: {description}")
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
    except (json.JSONDecodeError, TypeError) as exc:
        preview = content[:500] if content else "<empty>"
        logger.error(
            "Failed to parse LLM response as JSON (length=%d): %s\nContent preview: %s",
            len(content) if content else 0,
            exc,
            preview,
        )
    return []


def fetch_approved_entities(
    supabase: Any,
    use_case_id: str,
    entity_types: list[str],
) -> Any:
    """Fetch approved entities for a use case.

    Uses ``approved`` status as the authoritative signal — if an entity is
    approved it should be available to downstream workflows regardless of
    which run produced it.
    """
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
