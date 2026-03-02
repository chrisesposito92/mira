"""Compilation node — generates use case dicts from research results."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.prompts.use_case_gen import COMPILATION_PROMPT
from app.agents.state import UseCaseGenState

logger = logging.getLogger(__name__)


async def compile_use_cases(state: UseCaseGenState) -> dict:
    """Generate use case configurations from research and clarification context.

    Uses the LLM to transform research results into UseCaseCreate-compatible
    dicts, applying defaults for missing fields.
    """
    model_id = state["model_id"]
    customer_name = state["customer_name"]
    research_results = state.get("research_results", "")
    num_use_cases = state.get("num_use_cases", 1)
    notes = state.get("notes", "")
    attachment_text = state.get("attachment_text", "")
    clarification_answers = state.get("clarification_answers", [])

    # Build clarification context from answers
    clarification_context = "None"
    if clarification_answers:
        questions = state.get("clarification_questions", [])
        parts: list[str] = []
        for i, answer in enumerate(clarification_answers):
            q = questions[i]["question"] if i < len(questions) else f"Question {i + 1}"
            if isinstance(answer, dict):
                # Frontend sends {selected_option: <index>, free_text?: <str>}
                # Resolve the index to the option label from the question
                selected_idx = answer.get("selected_option")
                free_text = answer.get("free_text", "")
                if selected_idx is not None and i < len(questions):
                    opts = questions[i].get("options", [])
                    if 0 <= selected_idx < len(opts):
                        a = opts[selected_idx].get("label", str(selected_idx))
                    else:
                        a = str(selected_idx)
                elif free_text:
                    a = free_text
                else:
                    # Fallback for unexpected dict shapes
                    a = answer.get("selected", answer.get("label", str(answer)))
            else:
                a = str(answer)
            parts.append(f"Q: {q}\nA: {a}")
        clarification_context = "\n\n".join(parts)

    prompt = COMPILATION_PROMPT.format(
        customer_name=customer_name,
        research_results=research_results,
        num_use_cases=num_use_cases,
        notes=notes or "None provided",
        attachment_text=attachment_text or "None provided",
        clarification_context=clarification_context,
    )

    llm = get_llm(model_id, temperature=0.3)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=f"Generate {num_use_cases} use case(s) for {customer_name}."),
        ]
    )

    content = response.content if isinstance(response.content, str) else str(response.content)

    # Parse JSON array of use cases
    try:
        use_cases = json.loads(content)
        if not isinstance(use_cases, list):
            use_cases = [use_cases]
    except (json.JSONDecodeError, TypeError):
        logger.error("Failed to parse use case compilation output: %s", content[:200])
        use_cases = [
            {
                "title": f"{customer_name} Billing Use Case",
                "description": content,
            }
        ]

    # Validate and apply defaults
    validated: list[dict] = []
    for uc in use_cases:
        if not isinstance(uc, dict):
            continue
        if not uc.get("title") or not uc.get("description"):
            continue
        uc.setdefault("currency", "USD")
        uc.setdefault("billing_frequency", None)
        uc.setdefault("target_billing_model", None)
        uc.setdefault("notes", None)
        validated.append(uc)

    # Ensure at least one use case
    if not validated:
        validated = [
            {
                "title": f"{customer_name} Billing Use Case",
                "description": research_results or "No details available.",
                "currency": "USD",
                "billing_frequency": None,
                "target_billing_model": None,
                "notes": None,
            }
        ]

    return {
        "generated_use_cases": validated,
        "current_step": "compile_complete",
    }
