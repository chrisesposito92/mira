"""AccountPlan generation node."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.prompts.account_usage import ACCOUNT_PLAN_GENERATION_PROMPT
from app.agents.state import WorkflowState
from app.agents.utils import extract_llm_text, parse_entity_list

logger = logging.getLogger(__name__)


async def generate_account_plans(state: WorkflowState) -> dict:
    """Generate AccountPlan entity configurations using LLM.

    References approved accounts and plans for cross-linking.
    """
    model_id = state["model_id"]
    accounts = state.get("accounts", [])
    approved_plans = state.get("approved_plans", [])

    prompt = ACCOUNT_PLAN_GENERATION_PROMPT.format(
        accounts=json.dumps(accounts, indent=2),
        approved_plans=json.dumps(approved_plans, indent=2),
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the AccountPlan configurations now."),
        ]
    )

    content = extract_llm_text(response.content)
    account_plans = parse_entity_list(content)

    return {
        "account_plans": account_plans,
        "current_step": "account_plans_generated",
        "messages": state.get("messages", [])
        + [{"role": "assistant", "content": content, "step": "generate_account_plans"}],
    }
