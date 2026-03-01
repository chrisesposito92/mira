"""Pricing generation node."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.nodes.generation import _parse_entity_list
from app.agents.prompts.plan_pricing import PRICING_GENERATION_PROMPT
from app.agents.state import WorkflowState
from app.agents.utils import build_use_case_description

logger = logging.getLogger(__name__)


async def generate_pricing(state: WorkflowState) -> dict:
    """Generate Pricing entity configurations using LLM.

    References approved aggregations, plans, and plan templates for cross-linking.
    """
    model_id = state["model_id"]
    approved_aggregations = state.get("approved_aggregations", [])
    plans = state.get("plans", [])
    plan_templates = state.get("plan_templates", [])
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context", "")
    use_case = state.get("use_case", {})

    prompt = PRICING_GENERATION_PROMPT.format(
        approved_aggregations=json.dumps(approved_aggregations, indent=2),
        plans=json.dumps(plans, indent=2),
        plan_templates=json.dumps(plan_templates, indent=2),
        analysis=analysis if analysis else build_use_case_description(use_case),
        rag_context=rag_context,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the Pricing configurations now."),
        ]
    )

    content = response.content if isinstance(response.content, str) else str(response.content)
    pricing = _parse_entity_list(content)

    return {
        "pricing": pricing,
        "current_step": "pricing_generated",
        "messages": state.get("messages", [])
        + [{"role": "assistant", "content": content, "step": "generate_pricing"}],
    }
