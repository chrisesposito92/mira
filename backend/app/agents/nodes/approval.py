"""Approval node — persists entities as drafts, interrupts for user decisions."""

import json
import logging
from uuid import NAMESPACE_DNS, uuid5

from langgraph.types import interrupt

from app.agents.state import WorkflowState
from app.db.client import get_supabase_client
from app.schemas.common import EntityType, ObjectStatus

logger = logging.getLogger(__name__)

# Maps current step to entity/error/decision state keys + explicit approved step name
_STEP_CONFIG: dict[str, tuple[EntityType, str, str, str, str]] = {
    # step → (entity_type, entities_key, errors_key, decisions_key, approved_step)
    "products_validated": (
        EntityType.product,
        "products",
        "product_errors",
        "product_decisions",
        "products_approved",
    ),
    "meters_validated": (
        EntityType.meter,
        "meters",
        "meter_errors",
        "meter_decisions",
        "meters_approved",
    ),
    "aggregations_validated": (
        EntityType.aggregation,
        "aggregations",
        "aggregation_errors",
        "aggregation_decisions",
        "aggregations_approved",
    ),
    "plan_templates_validated": (
        EntityType.plan_template,
        "plan_templates",
        "plan_template_errors",
        "plan_template_decisions",
        "plan_templates_approved",
    ),
    "plans_validated": (
        EntityType.plan,
        "plans",
        "plan_errors",
        "plan_decisions",
        "plans_approved",
    ),
    "pricing_validated": (
        EntityType.pricing,
        "pricing",
        "pricing_errors",
        "pricing_decisions",
        "pricing_approved",
    ),
    "accounts_validated": (
        EntityType.account,
        "accounts",
        "account_errors",
        "account_decisions",
        "accounts_approved",
    ),
    "account_plans_validated": (
        EntityType.account_plan,
        "account_plans",
        "account_plan_errors",
        "account_plan_decisions",
        "account_plans_approved",
    ),
    "measurements_validated": (
        EntityType.measurement,
        "measurements",
        "measurement_errors",
        "measurement_decisions",
        "measurements_approved",
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

    entity_type, entities_key, errors_key, decisions_key, approved_step = config
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
        entity_name = entity.get("name", "")
        if not entity_name and entity_type == EntityType.pricing:
            pricing_type = entity.get("type", "pricing")
            desc = entity.get("description", "")
            entity_name = desc[:100] if desc else f"{pricing_type} pricing"
        if not entity_name and entity_type == EntityType.account_plan:
            account_id = entity.get("accountId", "")
            entity_name = f"AccountPlan: {account_id[:8]}"
        if not entity_name and entity_type == EntityType.measurement:
            entity_name = f"Measurement: {entity.get('uid', '')}"

        rows_to_insert.append(
            {
                "id": obj_id,
                "use_case_id": use_case_id,
                "entity_type": entity_type,
                "name": entity_name,
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
                # Only set name/code for entity types that have those fields;
                # AccountPlan and Measurement have neither.
                if entity_type not in (EntityType.account_plan, EntityType.measurement):
                    update_fields["name"] = edited_data.get("name", "")
                    update_fields["code"] = edited_data.get("code", "")
            supabase.table("generated_objects").update(update_fields).eq("id", obj_id).execute()

    # Promote undecided entities to approved in DB so state and DB stay consistent
    # (entities without explicit decisions flow through in state, so their DB rows
    # must not remain as draft)
    undecided_count = len(entity_ids) - len(decided_indices)
    if undecided_count > 0:
        logger.warning(
            "Auto-promoting %d undecided %s entities to approved (no explicit decision received)",
            undecided_count,
            entity_type,
        )
    for idx, obj_id in enumerate(entity_ids):
        if idx not in decided_indices:
            supabase.table("generated_objects").update({"status": ObjectStatus.approved}).eq(
                "id", obj_id
            ).execute()

    # Build mapping of entity to DB ID, filtering out rejected (None) entries
    entity_id_map = []
    for i, entity in enumerate(approved_entities):
        if entity is not None:
            entity_id_map.append((entity, entity_ids[i]))
    approved_entities = [e for e, _ in entity_id_map]
    for entity, db_id in entity_id_map:
        entity["id"] = db_id

    return {
        entities_key: approved_entities,
        decisions_key: decisions,
        "current_step": approved_step,
        "messages": state.get("messages", [])
        + [
            {
                "role": "assistant",
                "content": json.dumps(payload),
                "step": f"approve_{entity_type}",
            },
            {
                "role": "user",
                "content": json.dumps(decisions),
                "step": f"decision_{entity_type}",
            },
        ],
    }
