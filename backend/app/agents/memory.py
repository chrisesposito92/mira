"""Core memory module for LangGraph Store-based long-term memory.

Provides read/write operations for four memory use cases:
- UC1: Project-level domain knowledge (analysis context + correction patterns)
- UC2: User decision preferences (delegated to memory_decisions.py)
- UC3: Cross-workflow enrichment (workflow summaries)
- UC4: RAG enhancement feedback (delegated to memory_rag.py)

All store operations are wrapped in try/except — memory is additive, never required.
Functions return empty string on failure so workflows continue normally.

Namespace schema:
  ("project", {project_id}, "analysis")          — UC1
  ("project", {project_id}, "workflow_history")   — UC3
  ("user", {user_id}, "preferences", {entity_type}) — UC2
  ("project", {project_id}, "rag_feedback")       — UC4
"""

import asyncio
import logging

from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from app.agents.memory_decisions import format_preferences_for_prompt, retrieve_user_preferences

logger = logging.getLogger(__name__)


def get_store_from_config(config: RunnableConfig) -> BaseStore | None:
    """Safely extract the LangGraph Store from a RunnableConfig.

    Returns None if the store is unavailable (e.g. running without store,
    or config doesn't contain the expected runtime structure).
    """
    try:
        return config["configurable"]["__pregel_runtime"].store
    except (KeyError, AttributeError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Namespace helpers
# ---------------------------------------------------------------------------


def _analysis_namespace(project_id: str) -> tuple[str, ...]:
    return ("project", project_id, "analysis")


def _workflow_history_namespace(project_id: str) -> tuple[str, ...]:
    return ("project", project_id, "workflow_history")


# ---------------------------------------------------------------------------
# UC1: Project-level memory — write
# ---------------------------------------------------------------------------


async def save_analysis_context(
    store: BaseStore,
    project_id: str,
    use_case_id: str,
    analysis: str,
    use_case: dict,
) -> None:
    """Save analysis context for a use case to the project memory."""
    try:
        await store.aput(
            _analysis_namespace(project_id),
            f"analysis_{use_case_id}",
            {
                "analysis": analysis,
                "use_case_title": use_case.get("title", ""),
                "use_case_description": use_case.get("description", ""),
                "billing_model": use_case.get("target_billing_model", ""),
            },
        )
    except Exception:
        logger.warning("Failed to save analysis context for %s", use_case_id, exc_info=True)


async def save_user_corrections(
    store: BaseStore,
    project_id: str,
    use_case_id: str,
    entity_type: str,
    corrections: list[dict],
) -> None:
    """Save correction patterns (generated vs. edited diffs) to project memory.

    Capped at 50 corrections per use case + entity type combination.
    """
    if not corrections:
        return
    try:
        key = f"corrections_{use_case_id}_{entity_type}"
        existing = await store.aget(_analysis_namespace(project_id), key)
        existing_corrections = existing.value.get("corrections", []) if existing else []
        merged = (existing_corrections + corrections)[-50:]
        await store.aput(
            _analysis_namespace(project_id),
            key,
            {"corrections": merged, "entity_type": entity_type},
        )
    except Exception:
        logger.warning(
            "Failed to save corrections for %s/%s", use_case_id, entity_type, exc_info=True
        )


# ---------------------------------------------------------------------------
# UC1: Project-level memory — read
# ---------------------------------------------------------------------------


async def _fetch_analysis_items(store: BaseStore, project_id: str) -> list:
    """Fetch all analysis namespace items in a single store query."""
    try:
        return await store.asearch(_analysis_namespace(project_id), limit=50)
    except Exception:
        logger.warning("Failed to fetch analysis items for %s", project_id, exc_info=True)
        return []


def _format_project_context(items: list) -> str:
    """Format analysis items into a project context string."""
    analysis_items = [item for item in items if item.key.startswith("analysis_")]
    if not analysis_items:
        return ""
    parts = []
    for item in analysis_items[-10:]:
        val = item.value
        title = val.get("use_case_title", "Unknown")
        analysis = val.get("analysis", "")
        if analysis:
            parts.append(f"- [{title}]: {analysis[:500]}")
    if not parts:
        return ""
    return "Previous analyses for this project:\n" + "\n".join(parts)


def _format_correction_patterns(items: list) -> str:
    """Format correction items into a correction patterns string."""
    correction_items = [item for item in items if item.key.startswith("corrections_")]
    if not correction_items:
        return ""
    parts = []
    for item in correction_items[-10:]:
        val = item.value
        entity_type = val.get("entity_type", "")
        corrections = val.get("corrections", [])
        if corrections:
            summaries = [c.get("summary", str(c)) for c in corrections[-5:]]
            parts.append(f"- {entity_type}: {'; '.join(summaries)}")
    if not parts:
        return ""
    return (
        "User has previously corrected these patterns (apply similar adjustments):\n"
        + "\n".join(parts)
    )


async def load_project_context(store: BaseStore, project_id: str) -> str:
    """Load accumulated project-level domain knowledge as a prompt-injectable string."""
    items = await _fetch_analysis_items(store, project_id)
    return _format_project_context(items)


async def load_correction_patterns(store: BaseStore, project_id: str) -> str:
    """Load correction patterns from prior runs as a prompt-injectable string."""
    items = await _fetch_analysis_items(store, project_id)
    return _format_correction_patterns(items)


async def load_project_and_corrections(store: BaseStore, project_id: str) -> tuple[str, str]:
    """Load project context and correction patterns in a single store query.

    More efficient than calling load_project_context + load_correction_patterns
    separately, as it makes only one asearch call instead of two.
    """
    items = await _fetch_analysis_items(store, project_id)
    return _format_project_context(items), _format_correction_patterns(items)


# ---------------------------------------------------------------------------
# UC3: Cross-workflow enrichment — write
# ---------------------------------------------------------------------------


async def save_workflow_summary(
    store: BaseStore,
    project_id: str,
    use_case_id: str,
    workflow_num: int,
    entity_summary: str,
) -> None:
    """Save a concise workflow summary for cross-workflow enrichment.

    Key pattern: wf{N}_summary_{use_case_id} — re-running overwrites previous.
    """
    try:
        await store.aput(
            _workflow_history_namespace(project_id),
            f"wf{workflow_num}_summary_{use_case_id}",
            {"workflow_num": workflow_num, "summary": entity_summary, "use_case_id": use_case_id},
        )
    except Exception:
        logger.warning(
            "Failed to save WF%d summary for %s", workflow_num, use_case_id, exc_info=True
        )


# ---------------------------------------------------------------------------
# UC3: Cross-workflow enrichment — read
# ---------------------------------------------------------------------------


async def load_workflow_history(
    store: BaseStore,
    project_id: str,
    up_to_wf: int,
    use_case_id: str = "",
) -> str:
    """Load workflow summaries up to the given workflow number.

    Args:
        store: LangGraph store.
        project_id: Project ID for namespace scoping.
        up_to_wf: Only include summaries from workflows with number < up_to_wf.
        use_case_id: If provided, only include summaries for this use case.
            Prevents cross-use-case contamination in multi-use-case projects.

    Returns formatted string for prompt injection. Empty string if none found.
    """
    try:
        all_items = await store.asearch(_workflow_history_namespace(project_id), limit=50)
        items = [item for item in all_items if item.value.get("workflow_num", 0) < up_to_wf]
        if use_case_id:
            items = [item for item in items if item.value.get("use_case_id") == use_case_id]
        if not items:
            return ""
        items.sort(key=lambda x: x.value.get("workflow_num", 0))
        parts = []
        for item in items:
            val = item.value
            wf_num = val.get("workflow_num", 0)
            summary = val.get("summary", "")
            if summary:
                parts.append(f"Workflow {wf_num} output: {summary}")
        if not parts:
            return ""
        return "Context from prior workflows:\n" + "\n".join(parts)
    except Exception:
        logger.warning("Failed to load workflow history for %s", project_id, exc_info=True)
        return ""


# ---------------------------------------------------------------------------
# Helpers for building workflow summaries from entity state
# ---------------------------------------------------------------------------

_FINAL_STEPS: dict[str, int] = {
    "compound_aggregations_approved": 1,
    "pricing_approved": 2,
    "account_plans_approved": 3,
    "measurements_approved": 4,
}


def get_workflow_num_for_step(step: str) -> int | None:
    """Return the workflow number if this step is a final approval step, else None."""
    return _FINAL_STEPS.get(step)


def build_entity_summary(entities_key: str, entities: list[dict], entity_type: str) -> str:
    """Build a concise summary of approved entities for workflow history."""
    if not entities:
        return ""
    names = [e.get("name") or e.get("code") or "unnamed" for e in entities[:10]]
    return f"{entity_type} ({len(entities)}): {', '.join(names)}"


def build_workflow_summary_text(state: dict, workflow_num: int) -> str:
    """Build a complete workflow summary from state for the given workflow number."""
    parts = []
    if workflow_num == 1:
        for key, etype in [
            ("products", "Products"),
            ("meters", "Meters"),
            ("aggregations", "Aggregations"),
            ("compound_aggregations", "CompoundAggregations"),
        ]:
            s = build_entity_summary(key, state.get(key, []), etype)
            if s:
                parts.append(s)
    elif workflow_num == 2:
        for key, etype in [
            ("plan_templates", "PlanTemplates"),
            ("plans", "Plans"),
            ("pricing", "Pricing"),
        ]:
            s = build_entity_summary(key, state.get(key, []), etype)
            if s:
                parts.append(s)
    elif workflow_num == 3:
        for key, etype in [("accounts", "Accounts"), ("account_plans", "AccountPlans")]:
            s = build_entity_summary(key, state.get(key, []), etype)
            if s:
                parts.append(s)
    elif workflow_num == 4:
        s = build_entity_summary("measurements", state.get("measurements", []), "Measurements")
        if s:
            parts.append(s)

    analysis = state.get("analysis", "")
    if analysis:
        parts.append(f"Analysis: {analysis[:300]}")

    return "; ".join(parts) if parts else ""


def format_memory_section(label: str, content: str) -> str:
    """Format a memory section for prompt injection. Returns empty string if no content."""
    if not content:
        return ""
    return f"\n## {label}\n\n{content}\n"


def build_memory_context(
    project_memory: str = "",
    correction_patterns: str = "",
    user_preferences: str = "",
    workflow_history: str = "",
) -> dict[str, str]:
    """Build a dict of formatted memory sections for prompt placeholder injection."""
    return {
        "project_memory": format_memory_section("Project Memory", project_memory),
        "correction_patterns": format_memory_section("Correction Patterns", correction_patterns),
        "user_preferences": format_memory_section("User Preferences", user_preferences),
        "workflow_history": format_memory_section("Prior Workflow Context", workflow_history),
    }


# ---------------------------------------------------------------------------
# High-level helpers for node memory loading
# ---------------------------------------------------------------------------


async def load_enrichment_memory(
    config: RunnableConfig,
    project_id: str,
    up_to_wf: int,
    use_case_id: str = "",
) -> dict[str, str]:
    """Load memory context for cross-workflow enrichment (load_approved_* nodes).

    Args:
        config: RunnableConfig with store access.
        project_id: Project ID for namespace scoping.
        up_to_wf: Only include workflow summaries from workflows < up_to_wf.
        use_case_id: Scope workflow history to this use case to prevent
            cross-use-case contamination in multi-use-case projects.

    Returns dict with keys: workflow_history, project_memory, correction_patterns.
    Uses asyncio.gather for concurrent store reads.
    """
    store = get_store_from_config(config)
    if not store:
        return {"workflow_history": "", "project_memory": "", "correction_patterns": ""}

    pid = project_id or ""
    (project_memory, correction_patterns), workflow_history = await asyncio.gather(
        load_project_and_corrections(store, pid),
        load_workflow_history(store, pid, up_to_wf=up_to_wf, use_case_id=use_case_id),
    )
    return {
        "workflow_history": workflow_history,
        "project_memory": project_memory,
        "correction_patterns": correction_patterns,
    }


async def load_generation_memory(
    config: RunnableConfig,
    state: dict,
    entity_type: str,
    *,
    from_store: bool = False,
) -> dict[str, str]:
    """Load all memory context for a generation node.

    Args:
        config: RunnableConfig with store access.
        state: Current workflow state.
        entity_type: Entity type for user preference lookup.
        from_store: If True (WF1 nodes), loads project memory and corrections
            directly from store. If False (WF2+ nodes), reads them from state
            (pre-loaded by load_approved_* nodes).

    Returns dict of formatted memory sections for prompt placeholder injection.
    """
    store = get_store_from_config(config)

    if from_store and store:
        project_id = state.get("project_id", "")
        project_memory, correction_patterns = await load_project_and_corrections(store, project_id)
    else:
        project_memory = state.get("project_memory", "")
        correction_patterns = state.get("correction_patterns", "")

    workflow_history = state.get("workflow_history", "")

    user_preferences = ""
    if store:
        user_id = state.get("user_id", "")
        if user_id:
            prefs = await retrieve_user_preferences(store, user_id, entity_type)
            user_preferences = format_preferences_for_prompt(prefs)

    return build_memory_context(
        project_memory, correction_patterns, user_preferences, workflow_history
    )
