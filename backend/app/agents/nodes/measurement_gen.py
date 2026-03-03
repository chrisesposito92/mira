"""Measurement generation node."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.llm_factory import get_llm
from app.agents.memory import load_generation_memory
from app.agents.prompts.account_usage import MEASUREMENT_GENERATION_PROMPT
from app.agents.state import WorkflowState
from app.agents.utils import extract_llm_text, parse_entity_list

logger = logging.getLogger(__name__)


async def generate_measurements(state: WorkflowState, config: RunnableConfig) -> dict:
    """Generate sample Measurement data using LLM.

    References approved meters and accounts for cross-linking.
    """
    mem = await load_generation_memory(config, state, "measurement")

    model_id = state["model_id"]
    approved_meters = state.get("approved_meters", [])
    approved_accounts = state.get("approved_accounts", [])

    prompt = MEASUREMENT_GENERATION_PROMPT.format(
        approved_meters=json.dumps(approved_meters, indent=2),
        approved_accounts=json.dumps(approved_accounts, indent=2),
        **mem,
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

    messages = state.get("messages", []) + [
        {"role": "assistant", "content": content, "step": "generate_measurements"}
    ]

    if not measurements:
        return {
            "measurements": [],
            "current_step": "error",
            "error": (
                "Failed to generate measurements — the AI model returned an"
                " invalid response. Please try again or select a different model."
            ),
            "messages": messages,
        }

    return {
        "measurements": measurements,
        "current_step": "measurements_generated",
        "messages": messages,
    }
