"""Account generation node."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.llm_factory import get_llm
from app.agents.memory import load_generation_memory
from app.agents.prompts.account_usage import ACCOUNT_GENERATION_PROMPT
from app.agents.state import WorkflowState
from app.agents.utils import build_use_case_description, extract_llm_text, parse_entity_list

logger = logging.getLogger(__name__)


async def generate_accounts(state: WorkflowState, config: RunnableConfig) -> dict:
    """Generate Account entity configurations using LLM.

    References approved products and plans for context.
    """
    mem = await load_generation_memory(config, state, "account")

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
        **mem,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the Account configurations now."),
        ]
    )

    content = extract_llm_text(response.content)
    accounts = parse_entity_list(content)

    messages = state.get("messages", []) + [
        {"role": "assistant", "content": content, "step": "generate_accounts"}
    ]

    if not accounts:
        return {
            "accounts": [],
            "current_step": "error",
            "error": (
                "Failed to generate accounts — the AI model returned an"
                " invalid response. Please try again or select a different model."
            ),
            "messages": messages,
        }

    return {
        "accounts": accounts,
        "current_step": "accounts_generated",
        "messages": messages,
    }
