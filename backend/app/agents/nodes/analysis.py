"""Analysis node — fetches use case, retrieves RAG context, runs LLM analysis."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.prompts.product_meter import ANALYSIS_PROMPT
from app.agents.state import WorkflowState
from app.agents.tools.rag_tool import rag_retrieve
from app.db.client import get_supabase_client

logger = logging.getLogger(__name__)


async def analyze_use_case(state: WorkflowState) -> dict:
    """Analyze the use case to identify billing entities needed.

    1. Fetches use case details from the database.
    2. Retrieves relevant RAG context from m3ter docs + user docs.
    3. Runs LLM analysis to identify products, meters, and aggregations.
    4. Determines whether clarification questions are needed.
    """
    use_case_id = state["use_case_id"]
    model_id = state["model_id"]
    project_id = state.get("project_id")

    # Fetch use case from database
    supabase = get_supabase_client()
    result = supabase.table("use_cases").select("*").eq("id", use_case_id).execute()
    if not result.data:
        return {"error": f"Use case {use_case_id} not found", "current_step": "error"}
    use_case = result.data[0]

    # Build use case description for RAG query and prompt
    description_parts = [use_case.get("title", "")]
    if use_case.get("description"):
        description_parts.append(use_case["description"])
    if use_case.get("target_billing_model"):
        description_parts.append(f"Target billing model: {use_case['target_billing_model']}")
    if use_case.get("billing_frequency"):
        description_parts.append(f"Billing frequency: {use_case['billing_frequency']}")
    if use_case.get("notes"):
        description_parts.append(f"Notes: {use_case['notes']}")
    use_case_description = "\n".join(description_parts)

    # Retrieve RAG context
    rag_context = await rag_retrieve(
        query=f"m3ter billing configuration for: {use_case_description}",
        project_id=project_id,
        k=5,
    )

    # Format the analysis prompt
    prompt = ANALYSIS_PROMPT.format(
        rag_context=rag_context,
        use_case_description=use_case_description,
    )

    # Run LLM analysis
    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Analyze this use case and provide your assessment."),
        ]
    )

    # Parse LLM response
    try:
        parsed = json.loads(response.content)
        analysis = parsed.get("analysis", response.content)
        needs_clarification = parsed.get("needs_clarification", False)
    except (json.JSONDecodeError, TypeError):
        analysis = response.content if isinstance(response.content, str) else str(response.content)
        needs_clarification = False

    return {
        "use_case": use_case,
        "rag_context": rag_context,
        "analysis": analysis,
        "needs_clarification": needs_clarification,
        "current_step": "analysis_complete",
        "messages": state.get("messages", [])
        + [{"role": "assistant", "content": analysis, "step": "analysis"}],
    }
