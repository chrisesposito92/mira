"""Pricing generation node."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.llm_factory import get_llm
from app.agents.memory import load_generation_memory
from app.agents.prompts.plan_pricing import PRICING_GENERATION_PROMPT
from app.agents.state import WorkflowState
from app.agents.utils import (
    build_use_case_description,
    extract_llm_text,
    inject_parent_references,
    parse_entity_list,
)

logger = logging.getLogger(__name__)


async def generate_pricing(state: WorkflowState, config: RunnableConfig) -> dict:
    """Generate Pricing entity configurations using LLM.

    References approved aggregations, plans, and plan templates for cross-linking.
    """
    mem = await load_generation_memory(config, state, "pricing")

    model_id = state["model_id"]
    approved_aggregations = state.get("approved_aggregations", [])
    approved_compound_aggregations = state.get("approved_compound_aggregations", [])
    plans = state.get("plans", [])
    plan_templates = state.get("plan_templates", [])
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context", "")
    use_case = state.get("use_case", {})

    prompt = PRICING_GENERATION_PROMPT.format(
        approved_aggregations=json.dumps(approved_aggregations, indent=2),
        approved_compound_aggregations=json.dumps(approved_compound_aggregations, indent=2),
        plans=json.dumps(plans, indent=2),
        plan_templates=json.dumps(plan_templates, indent=2),
        analysis=analysis if analysis else build_use_case_description(use_case),
        rag_context=rag_context,
        **mem,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the Pricing configurations now."),
        ]
    )

    content = extract_llm_text(response.content)
    pricing = parse_entity_list(content)

    # Inject aggregationId from approved aggregations (regular + compound)
    all_aggregations = list(approved_aggregations) + list(approved_compound_aggregations)
    if pricing and all_aggregations:
        inject_parent_references(
            pricing, "aggregationId", all_aggregations, code_hint_field="aggregationCode"
        )
        # Also handle compoundAggregationId if present
        inject_parent_references(
            pricing,
            "compoundAggregationId",
            approved_compound_aggregations,
            code_hint_field="compoundAggregationCode",
        )

    # Inject planTemplateId from plan templates
    if pricing and plan_templates:
        inject_parent_references(
            pricing, "planTemplateId", plan_templates, code_hint_field="planTemplateCode"
        )

    # Inject planId from plans (some pricing uses planId instead)
    if pricing and plans:
        inject_parent_references(pricing, "planId", plans, code_hint_field="planCode")

    messages = state.get("messages", []) + [
        {"role": "assistant", "content": content, "step": "generate_pricing"}
    ]

    if not pricing:
        return {
            "pricing": [],
            "current_step": "error",
            "error": (
                "Failed to generate pricing — the AI model returned an"
                " invalid response. Please try again or select a different model."
            ),
            "messages": messages,
        }

    return {
        "pricing": pricing,
        "current_step": "pricing_generated",
        "messages": messages,
    }
