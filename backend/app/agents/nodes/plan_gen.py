"""Plan generation node."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.llm_factory import get_llm
from app.agents.memory import load_generation_memory
from app.agents.prompts.plan_pricing import PLAN_GENERATION_PROMPT
from app.agents.state import WorkflowState
from app.agents.utils import (
    build_use_case_description,
    extract_llm_text,
    inject_parent_references,
    parse_entity_list,
)

logger = logging.getLogger(__name__)


async def generate_plans(state: WorkflowState, config: RunnableConfig) -> dict:
    """Generate Plan entity configurations using LLM.

    References approved products and plan templates for cross-linking.
    """
    mem = await load_generation_memory(config, state, "plan")

    model_id = state["model_id"]
    approved_products = state.get("approved_products", [])
    plan_templates = state.get("plan_templates", [])
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context", "")
    use_case = state.get("use_case", {})

    prompt = PLAN_GENERATION_PROMPT.format(
        approved_products=json.dumps(approved_products, indent=2),
        plan_templates=json.dumps(plan_templates, indent=2),
        analysis=analysis if analysis else build_use_case_description(use_case),
        rag_context=rag_context,
        **mem,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the Plan configurations now."),
        ]
    )

    content = extract_llm_text(response.content)
    plans = parse_entity_list(content)

    # Inject planTemplateId from approved plan templates
    if plans and plan_templates:
        inject_parent_references(
            plans, "planTemplateId", plan_templates, code_hint_field="planTemplateCode"
        )

    messages = state.get("messages", []) + [
        {"role": "assistant", "content": content, "step": "generate_plans"}
    ]

    if not plans:
        return {
            "plans": [],
            "current_step": "error",
            "error": (
                "Failed to generate plans — the AI model returned an"
                " invalid response. Please try again or select a different model."
            ),
            "messages": messages,
        }

    return {
        "plans": plans,
        "current_step": "plans_generated",
        "messages": messages,
    }
