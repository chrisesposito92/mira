"""Load approved entities from Workflow 1 for use in Workflow 2."""

import logging

from app.agents.state import WorkflowState
from app.agents.tools.rag_tool import rag_retrieve
from app.agents.utils import build_use_case_description
from app.db.client import get_supabase_client
from app.schemas.common import EntityType, ObjectStatus, WorkflowStatus, WorkflowType

logger = logging.getLogger(__name__)


async def load_approved_entities(state: WorkflowState) -> dict:
    """Load approved Products/Meters/Aggregations from DB.

    Fetches all approved entities from Workflow 1 and the use case data,
    then retrieves RAG context for plan/pricing generation.
    """
    use_case_id = state.get("use_case_id", "")
    project_id = state.get("project_id")
    supabase = get_supabase_client()

    # Find the latest completed WF1 to scope entity fetch
    wf1_result = (
        supabase.table("workflows")
        .select("started_at")
        .eq("use_case_id", use_case_id)
        .eq("workflow_type", WorkflowType.product_meter_aggregation)
        .eq("status", WorkflowStatus.completed)
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )

    # Fetch approved entities scoped to the latest WF1 run
    query = (
        supabase.table("generated_objects")
        .select("entity_type, data")
        .eq("use_case_id", use_case_id)
        .eq("status", ObjectStatus.approved)
        .in_(
            "entity_type",
            [EntityType.product, EntityType.meter, EntityType.aggregation],
        )
    )
    if wf1_result.data:
        wf1_started_at = wf1_result.data[0]["started_at"]
        query = query.gte("created_at", wf1_started_at)

    result = query.execute()

    approved_products: list[dict] = []
    approved_meters: list[dict] = []
    approved_aggregations: list[dict] = []

    for row in result.data:
        entity_data = row.get("data", {})
        entity_type = row.get("entity_type")
        if entity_type == EntityType.product:
            approved_products.append(entity_data)
        elif entity_type == EntityType.meter:
            approved_meters.append(entity_data)
        elif entity_type == EntityType.aggregation:
            approved_aggregations.append(entity_data)

    # Fetch use case data
    uc_result = (
        supabase.table("use_cases")
        .select("title, description, industry, target_billing_model")
        .eq("id", use_case_id)
        .execute()
    )
    use_case = uc_result.data[0] if uc_result.data else {}
    use_case_description = build_use_case_description(use_case)

    # Retrieve RAG context for plan/pricing generation
    rag_context = ""
    try:
        rag_context = await rag_retrieve(
            query=f"m3ter plan template pricing configuration for: {use_case_description}",
            project_id=project_id,
            k=5,
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

    return {
        "approved_products": approved_products,
        "approved_meters": approved_meters,
        "approved_aggregations": approved_aggregations,
        "use_case": use_case,
        "rag_context": rag_context,
        "current_step": "approved_entities_loaded",
    }
