"""Load approved entities from Workflows 1 and 2 for use in Workflow 3 (Account Setup)."""

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


async def load_approved_for_accounts(state: WorkflowState, config: RunnableConfig) -> dict:
    """Load approved entities from WF1 and WF2 for account generation.

    Fetches Products, Meters, Aggregations (from WF1) and PlanTemplates,
    Plans, Pricing (from WF2), plus use case data and RAG context.
    """
    use_case_id = state.get("use_case_id", "")
    project_id = state.get("project_id")
    supabase = get_supabase_client()

    # Fetch WF1 approved entities (products, meters, aggregations)
    wf1_entities = fetch_approved_entities(
        supabase,
        use_case_id,
        [EntityType.product, EntityType.meter, EntityType.aggregation],
    )

    # Fetch WF2 approved entities (plan_templates, plans, pricing)
    wf2_entities = fetch_approved_entities(
        supabase,
        use_case_id,
        [EntityType.plan_template, EntityType.plan, EntityType.pricing],
    )

    # Sort entities into buckets, injecting canonical IDs
    approved_products: list[dict] = []
    approved_meters: list[dict] = []
    approved_aggregations: list[dict] = []
    approved_plan_templates: list[dict] = []
    approved_plans: list[dict] = []
    approved_pricing: list[dict] = []

    for row in wf1_entities.data:
        entity_data = inject_entity_id(row)
        entity_type = row.get("entity_type")
        if entity_type == EntityType.product:
            approved_products.append(entity_data)
        elif entity_type == EntityType.meter:
            approved_meters.append(entity_data)
        elif entity_type == EntityType.aggregation:
            approved_aggregations.append(entity_data)

    for row in wf2_entities.data:
        entity_data = inject_entity_id(row)
        entity_type = row.get("entity_type")
        if entity_type == EntityType.plan_template:
            approved_plan_templates.append(entity_data)
        elif entity_type == EntityType.plan:
            approved_plans.append(entity_data)
        elif entity_type == EntityType.pricing:
            approved_pricing.append(entity_data)

    # Plans are required — AccountPlan generation needs valid plan IDs
    if not approved_plans:
        return {
            "error": (
                "No approved plans found from Workflow 2. "
                "Plans are required to generate account plans."
            ),
            "current_step": "error",
        }

    if not approved_products:
        return {
            "error": (
                "No approved products found from Workflow 1. "
                "Products are required to generate accounts."
            ),
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

    # Retrieve RAG context (with feedback re-ranking)
    from app.agents.memory import get_store_from_config

    store = get_store_from_config(config)
    rag_context = ""
    try:
        rag_context = await rag_retrieve(
            query=f"m3ter account setup billing configuration for: {use_case_description}",
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
        "Loaded approved entities for account setup (use case %s): "
        "%d products, %d meters, %d aggregations, "
        "%d plan_templates, %d plans, %d pricing",
        use_case_id,
        len(approved_products),
        len(approved_meters),
        len(approved_aggregations),
        len(approved_plan_templates),
        len(approved_plans),
        len(approved_pricing),
    )

    # Load memory context from store
    mem = await load_enrichment_memory(config, project_id, up_to_wf=3)

    return {
        "approved_products": approved_products,
        "approved_meters": approved_meters,
        "approved_aggregations": approved_aggregations,
        "approved_plan_templates": approved_plan_templates,
        "approved_plans": approved_plans,
        "approved_pricing": approved_pricing,
        "use_case": use_case,
        "rag_context": rag_context,
        **mem,
        "current_step": "approved_entities_loaded_for_accounts",
    }
