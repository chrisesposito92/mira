"""Clarification node for use case generator — disambiguates company identity."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt

from app.agents.llm_factory import get_llm
from app.agents.prompts.use_case_gen import CLARIFICATION_PROMPT
from app.agents.state import UseCaseGenState

logger = logging.getLogger(__name__)

# Cache generated questions by thread_id so that LangGraph's node re-execution
# on interrupt resume reuses the exact questions the user originally answered.
_question_cache: dict[str, list[dict]] = {}


async def ask_clarification(state: UseCaseGenState) -> dict:
    """Generate clarification questions and interrupt for user input.

    Follows the same pattern as the main workflow clarification node:
    questions are cached by thread_id so the re-execution on resume
    produces the same questions the user answered.
    """
    model_id = state["model_id"]
    customer_name = state["customer_name"]
    research_results = state.get("research_results", "")
    thread_id = state.get("thread_id", "")
    cache_key = f"{thread_id}:use_case_gen_clarification"

    questions = _question_cache.get(cache_key)
    if questions is None:
        prompt = CLARIFICATION_PROMPT.format(
            customer_name=customer_name,
            research_results=research_results,
        )
        llm = get_llm(model_id, temperature=0.3)
        response = await llm.ainvoke(
            [
                SystemMessage(content=prompt),
                HumanMessage(
                    content="Generate clarification questions to disambiguate the company."
                ),
            ]
        )

        try:
            content = (
                response.content if isinstance(response.content, str) else str(response.content)
            )
            questions = json.loads(content)
            if not isinstance(questions, list):
                questions = [questions]
        except (json.JSONDecodeError, TypeError):
            questions = [
                {
                    "question": f"Which '{customer_name}' company do you mean?",
                    "options": [
                        {"label": "Not sure", "description": "Please provide more context"},
                    ],
                    "recommendation": "Not sure",
                }
            ]

        _question_cache[cache_key] = questions

    # Interrupt the graph to wait for user answers
    user_response = interrupt(
        {
            "type": "gen_clarification",
            "questions": questions,
        }
    )

    # Clean up cache after successful resume
    _question_cache.pop(cache_key, None)

    # Process the answers from the user's resume command
    answers = user_response if isinstance(user_response, list) else [user_response]

    return {
        "clarification_questions": questions,
        "clarification_answers": answers,
        "needs_clarification": False,
        "current_step": "clarification_complete",
    }


def cleanup_question_cache(thread_id: str) -> None:
    """Remove cached questions for the given thread_id (call on session teardown)."""
    key = f"{thread_id}:use_case_gen_clarification"
    _question_cache.pop(key, None)
