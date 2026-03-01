"""PlanTemplate generation node."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.prompts.plan_pricing import PLAN_TEMPLATE_GENERATION_PROMPT
from app.agents.state import WorkflowState
from app.agents.utils import build_use_case_description, parse_entity_list

logger = logging.getLogger(__name__)


async def generate_plan_templates(state: WorkflowState) -> dict:
    """Generate PlanTemplate entity configurations using LLM.

    References approved products from Workflow 1.
    """
    model_id = state["model_id"]
    approved_products = state.get("approved_products", [])
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context", "")
    use_case = state.get("use_case", {})

    prompt = PLAN_TEMPLATE_GENERATION_PROMPT.format(
        approved_products=json.dumps(approved_products, indent=2),
        analysis=analysis if analysis else build_use_case_description(use_case),
        rag_context=rag_context,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the PlanTemplate configurations now."),
        ]
    )

    content = response.content if isinstance(response.content, str) else str(response.content)
    plan_templates = parse_entity_list(content)

    return {
        "plan_templates": plan_templates,
        "current_step": "plan_templates_generated",
        "messages": state.get("messages", [])
        + [{"role": "assistant", "content": content, "step": "generate_plan_templates"}],
    }
