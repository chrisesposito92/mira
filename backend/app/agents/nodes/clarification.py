"""Clarification nodes — generates questions and processes user answers."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt

from app.agents.llm_factory import get_llm
from app.agents.prompts.product_meter import CLARIFICATION_PROMPT
from app.agents.state import WorkflowState

logger = logging.getLogger(__name__)

# Cache generated questions by use_case_id so that LangGraph's node re-execution
# on interrupt resume reuses the exact questions the user originally answered
# (answers are index-based, so regenerated questions would cause mismatches).
_question_cache: dict[str, list] = {}


async def generate_clarifications(state: WorkflowState) -> dict:
    """Generate clarification questions and interrupt for user input.

    Uses the LLM to produce targeted multiple-choice questions based on the
    analysis, then pauses the graph via interrupt() so the user can respond.

    Questions are cached by use_case_id so that the inevitable re-execution on
    resume produces the same questions the user answered (interrupt answers are
    index-based).
    """
    analysis = state.get("analysis", "")
    model_id = state["model_id"]
    use_case_id = state.get("use_case_id", "")
    cache_key = f"{use_case_id}:clarification"

    questions = _question_cache.get(cache_key)
    if questions is None:
        prompt = CLARIFICATION_PROMPT.format(analysis=analysis)
        llm = get_llm(model_id, temperature=0.3)
        response = await llm.ainvoke(
            [
                SystemMessage(content=prompt),
                HumanMessage(content="Generate clarification questions for this use case."),
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
                    "question": "Could you provide more details about the billing model?",
                    "options": [
                        {"label": "Usage-based", "description": "Charge based on consumption"},
                        {"label": "Subscription", "description": "Fixed recurring charge"},
                        {"label": "Hybrid", "description": "Combination of usage and subscription"},
                    ],
                    "recommendation": "Usage-based",
                }
            ]

        _question_cache[cache_key] = questions

    # Interrupt the graph to wait for user answers
    user_response = interrupt(
        {
            "type": "clarification",
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
        "messages": state.get("messages", [])
        + [
            {"role": "assistant", "content": json.dumps(questions), "step": "clarification_ask"},
            {"role": "user", "content": json.dumps(answers), "step": "clarification_answer"},
        ],
    }
