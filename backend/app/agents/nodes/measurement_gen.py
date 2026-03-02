"""Measurement generation node."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.prompts.account_usage import MEASUREMENT_GENERATION_PROMPT
from app.agents.state import WorkflowState
from app.agents.utils import extract_llm_text, parse_entity_list

logger = logging.getLogger(__name__)


async def generate_measurements(state: WorkflowState) -> dict:
    """Generate sample Measurement data using LLM.

    References approved meters and accounts for cross-linking.
    """
    model_id = state["model_id"]
    approved_meters = state.get("approved_meters", [])
    approved_accounts = state.get("approved_accounts", [])

    prompt = MEASUREMENT_GENERATION_PROMPT.format(
        approved_meters=json.dumps(approved_meters, indent=2),
        approved_accounts=json.dumps(approved_accounts, indent=2),
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the sample Measurement data now."),
        ]
    )

    content = extract_llm_text(response.content)
    measurements = parse_entity_list(content)

    return {
        "measurements": measurements,
        "current_step": "measurements_generated",
        "messages": state.get("messages", [])
        + [{"role": "assistant", "content": content, "step": "generate_measurements"}],
    }
