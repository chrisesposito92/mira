"""Approval node — persists entities as drafts, interrupts for user decisions."""

import json
import logging
from uuid import NAMESPACE_DNS, uuid5

from langgraph.types import interrupt

from app.agents.state import WorkflowState
from app.db.client import get_supabase_client
from app.schemas.common import EntityType, ObjectStatus

logger = logging.getLogger(__name__)

# Maps current step to entity/error/decision state keys
_STEP_CONFIG: dict[str, tuple[EntityType, str, str, str]] = {
    # step → (entity_type, entities_key, errors_key, decisions_key)
    "products_validated": (EntityType.product, "products", "product_errors", "product_decisions"),
    "meters_validated": (EntityType.meter, "meters", "meter_errors", "meter_decisions"),
    "aggregations_validated": (
        EntityType.aggregation,
        "aggregations",
        "aggregation_errors",
        "aggregation_decisions",
    ),
}


async def approve_entities(state: WorkflowState) -> dict:
    """Present entities for approval and process user decisions.

    1. Reads the current entity batch and validation errors from state.
    2. Interrupts the graph with the entity payload for user review.
    3. On resume, persists entities to generated_objects as drafts (batch insert).
    4. Processes approve/reject/edit decisions.

    DB insert is deferred until after interrupt() returns because LangGraph
    re-executes the node from the top on resume — inserting before interrupt
    would create duplicate rows on every resume.
    """
    current_step = state.get("current_step", "")
    config = _STEP_CONFIG.get(current_step)
    if not config:
        logger.warning("approve_entities called with unexpected step: %s", current_step)
        return {}

    entity_type, entities_key, errors_key, decisions_key = config
    entities = state.get(entities_key, [])
    errors = state.get(errors_key, [])
    use_case_id = state.get("use_case_id", "")
    thread_id = state.get("thread_id", "")

    # Build interrupt payload (no DB insert yet — LangGraph re-executes the node
    # from the top on resume, so inserting before interrupt() would create duplicates)
    payload = {
        "type": "entities",
        "entity_type": entity_type,
        "entities": [{"index": i, **entity} for i, entity in enumerate(entities)],
        "errors": errors,
    }

    # Interrupt for user approval — on resume, returns the user's decisions
    user_response = interrupt(payload)

    # --- Everything below only executes on resume ---

    # Persist entities as drafts and process decisions
    supabase = get_supabase_client()
    decisions = user_response if isinstance(user_response, list) else [user_response]

    entity_ids: list[str] = []
    rows_to_insert = []
    for i, entity in enumerate(entities):
        obj_id = str(uuid5(NAMESPACE_DNS, f"{thread_id}:{entity_type}:{i}"))
        entity_ids.append(obj_id)
        rows_to_insert.append(
            {
                "id": obj_id,
                "use_case_id": use_case_id,
                "entity_type": entity_type,
                "name": entity.get("name", ""),
                "code": entity.get("code", ""),
                "status": ObjectStatus.draft,
                "data": entity,
            }
        )

    if rows_to_insert:
        supabase.table("generated_objects").upsert(rows_to_insert).execute()

    approved_entities = list(entities)
    decided_indices: set[int] = set()

    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        idx = decision.get("index", 0)
        action = decision.get("action", "approve")

        if idx < 0 or idx >= len(entity_ids):
            continue

        decided_indices.add(idx)
        obj_id = entity_ids[idx]

        if action == "approve":
            supabase.table("generated_objects").update({"status": ObjectStatus.approved}).eq(
                "id", obj_id
            ).execute()

        elif action == "reject":
            supabase.table("generated_objects").update({"status": ObjectStatus.rejected}).eq(
                "id", obj_id
            ).execute()
            if idx < len(approved_entities):
                approved_entities[idx] = None  # type: ignore[call-overload]

        elif action == "edit":
            edited_data = decision.get("data", {})
            if edited_data and idx < len(approved_entities):
                approved_entities[idx] = edited_data
            update_fields: dict = {"status": ObjectStatus.approved}
            if edited_data:
                update_fields["data"] = edited_data
                update_fields["name"] = edited_data.get("name", "")
                update_fields["code"] = edited_data.get("code", "")
            supabase.table("generated_objects").update(update_fields).eq("id", obj_id).execute()

    # Promote undecided entities to approved in DB so state and DB stay consistent
    # (entities without explicit decisions flow through in state, so their DB rows
    # must not remain as draft)
    for idx, obj_id in enumerate(entity_ids):
        if idx not in decided_indices:
            supabase.table("generated_objects").update({"status": ObjectStatus.approved}).eq(
                "id", obj_id
            ).execute()

    # Filter out rejected entities (None entries)
    approved_entities = [e for e in approved_entities if e is not None]

    return {
        entities_key: approved_entities,
        decisions_key: decisions,
        "current_step": f"{entity_type}s_approved",
        "messages": state.get("messages", [])
        + [
            {
                "role": "assistant",
                "content": json.dumps(payload),
                "step": f"approve_{entity_type}s",
            },
            {
                "role": "user",
                "content": json.dumps(decisions),
                "step": f"decision_{entity_type}s",
            },
        ],
    }
