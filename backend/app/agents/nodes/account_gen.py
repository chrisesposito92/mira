"""Account generation node."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.prompts.account_usage import ACCOUNT_GENERATION_PROMPT
from app.agents.state import WorkflowState
from app.agents.utils import build_use_case_description, parse_entity_list

logger = logging.getLogger(__name__)


async def generate_accounts(state: WorkflowState) -> dict:
    """Generate Account entity configurations using LLM.

    References approved products and plans for context.
    """
    model_id = state["model_id"]
    approved_products = state.get("approved_products", [])
    approved_plans = state.get("approved_plans", [])
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context", "")
    use_case = state.get("use_case", {})

    prompt = ACCOUNT_GENERATION_PROMPT.format(
        approved_products=json.dumps(approved_products, indent=2),
        approved_plans=json.dumps(approved_plans, indent=2),
        analysis=analysis if analysis else build_use_case_description(use_case),
        rag_context=rag_context,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the Account configurations now."),
        ]
    )

    content = response.content if isinstance(response.content, str) else str(response.content)
    accounts = parse_entity_list(content)

    return {
        "accounts": accounts,
        "current_step": "accounts_generated",
        "messages": state.get("messages", [])
        + [{"role": "assistant", "content": content, "step": "generate_accounts"}],
    }
