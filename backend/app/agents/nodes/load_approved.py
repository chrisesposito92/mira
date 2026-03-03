"""Load approved entities from Workflow 1 for use in Workflow 2."""

import logging

from langchain_core.runnables import RunnableConfig

from app.agents.memory import load_enrichment_memory
from app.agents.state import WorkflowState
from app.agents.tools.rag_tool import rag_retrieve
from app.agents.utils import (
    build_use_case_description,
    fetch_approved_entities,
    inject_entity_id,
)
from app.db.client import get_supabase_client
from app.schemas.common import EntityType

logger = logging.getLogger(__name__)


async def load_approved_entities(state: WorkflowState, config: RunnableConfig) -> dict:
    """Load approved Products/Meters/Aggregations from DB.

    Fetches all approved entities from Workflow 1 and the use case data,
    then retrieves RAG context for plan/pricing generation.
    """
    use_case_id = state.get("use_case_id", "")
    project_id = state.get("project_id")
    supabase = get_supabase_client()

    # Fetch all approved entities for this use case (no time-window scoping)
    result = fetch_approved_entities(
        supabase,
        use_case_id,
        [EntityType.product, EntityType.meter, EntityType.aggregation],
    )

    approved_products: list[dict] = []
    approved_meters: list[dict] = []
    approved_aggregations: list[dict] = []

    for row in result.data:
        entity_data = inject_entity_id(row)
        entity_type = row.get("entity_type")
        if entity_type == EntityType.product:
            approved_products.append(entity_data)
        elif entity_type == EntityType.meter:
            approved_meters.append(entity_data)
        elif entity_type == EntityType.aggregation:
            approved_aggregations.append(entity_data)

    if not approved_products and not approved_meters and not approved_aggregations:
        return {
            "error": "No approved entities found from Workflow 1. Cannot generate plans/pricing.",
            "current_step": "error",
        }

    # Fetch use case data
    uc_result = (
        supabase.table("use_cases")
        .select("title, description, target_billing_model")
        .eq("id", use_case_id)
        .execute()
    )
    use_case = uc_result.data[0] if uc_result.data else {}
    use_case_description = build_use_case_description(use_case)

    # Retrieve RAG context for plan/pricing generation (with feedback re-ranking)
    from app.agents.memory import get_store_from_config

    store = get_store_from_config(config)
    rag_context = ""
    try:
        rag_context = await rag_retrieve(
            query=f"m3ter plan template pricing configuration for: {use_case_description}",
            project_id=project_id,
            k=5,
            store=store,
        )
    except Exception:
        logger.warning(
            "RAG retrieval failed for use case %s, continuing without RAG context",
            use_case_id,
            exc_info=True,
        )

    logger.info(
        "Loaded approved entities for use case %s: %d products, %d meters, %d aggregations",
        use_case_id,
        len(approved_products),
        len(approved_meters),
        len(approved_aggregations),
    )

    # Load memory context from store
    mem = await load_enrichment_memory(config, project_id, up_to_wf=2, use_case_id=use_case_id)

    return {
        "approved_products": approved_products,
        "approved_meters": approved_meters,
        "approved_aggregations": approved_aggregations,
        "use_case": use_case,
        "rag_context": rag_context,
        **mem,
        "current_step": "approved_entities_loaded",
    }
