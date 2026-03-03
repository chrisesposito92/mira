"""Load approved entities from Workflows 1 and 3 for use in Workflow 4 (Usage Submission)."""

import logging

from langchain_core.runnables import RunnableConfig

from app.agents.memory import load_enrichment_memory
from app.agents.state import WorkflowState
from app.agents.utils import (
    fetch_approved_entities,
    inject_entity_id,
)
from app.db.client import get_supabase_client
from app.schemas.common import EntityType

logger = logging.getLogger(__name__)


async def load_approved_for_usage(state: WorkflowState, config: RunnableConfig) -> dict:
    """Load approved Meters (WF1) and Accounts (WF3) for measurement generation.

    No RAG context is needed for measurement generation since measurements
    are simple data submissions using existing meter and account codes.
    """
    use_case_id = state.get("use_case_id", "")
    supabase = get_supabase_client()

    # Fetch approved meters from WF1
    meters_result = fetch_approved_entities(supabase, use_case_id, [EntityType.meter])

    # Fetch approved accounts from WF3
    accounts_result = fetch_approved_entities(supabase, use_case_id, [EntityType.account])

    approved_meters = [inject_entity_id(row) for row in meters_result.data]
    approved_accounts = [inject_entity_id(row) for row in accounts_result.data]

    if not approved_meters or not approved_accounts:
        missing = []
        if not approved_meters:
            missing.append("meters")
        if not approved_accounts:
            missing.append("accounts")
        return {
            "error": (
                f"Missing approved {' and '.join(missing)}. "
                "Both meters and accounts are required to generate measurements."
            ),
            "current_step": "error",
        }

    logger.info(
        "Loaded approved entities for usage submission (use case %s): %d meters, %d accounts",
        use_case_id,
        len(approved_meters),
        len(approved_accounts),
    )

    # Load memory context from store
    project_id = state.get("project_id", "")
    mem = await load_enrichment_memory(config, project_id, up_to_wf=4, use_case_id=use_case_id)

    return {
        "approved_meters": approved_meters,
        "approved_accounts": approved_accounts,
        **mem,
        "current_step": "approved_entities_loaded_for_usage",
    }
