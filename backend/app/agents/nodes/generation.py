"""Generation nodes — produce Products, Meters, and Aggregation configs via LLM."""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.llm_factory import get_llm
from app.agents.memory import load_generation_memory
from app.agents.prompts.product_meter import (
    AGGREGATION_GENERATION_PROMPT,
    COMPOUND_AGGREGATION_GENERATION_PROMPT,
    METER_GENERATION_PROMPT,
    PRODUCT_GENERATION_PROMPT,
)
from app.agents.state import WorkflowState
from app.agents.utils import extract_llm_text, inject_parent_references, parse_entity_list

logger = logging.getLogger(__name__)


def _format_clarification_answers(state: WorkflowState) -> str:
    """Format clarification answers for prompt injection."""
    answers = state.get("clarification_answers", [])
    questions = state.get("clarification_questions", [])
    if not answers:
        return "No clarification was needed."

    parts = []
    for i, answer in enumerate(answers):
        question_text = ""
        if i < len(questions):
            question_text = questions[i].get("question", f"Question {i + 1}")
        if isinstance(answer, dict):
            if answer.get("selected_option") is not None and i < len(questions):
                options = questions[i].get("options", [])
                idx = answer["selected_option"]
                if 0 <= idx < len(options):
                    parts.append(f"Q: {question_text}\nA: {options[idx].get('label', str(idx))}")
                    continue
            if answer.get("free_text"):
                parts.append(f"Q: {question_text}\nA: {answer['free_text']}")
                continue
        parts.append(f"Q: {question_text}\nA: {answer}")

    return "\n\n".join(parts) if parts else "No clarification was needed."


async def generate_products(state: WorkflowState, config: RunnableConfig) -> dict:
    """Generate Product entity configurations using LLM."""
    mem = await load_generation_memory(config, state, "product", from_store=True)

    model_id = state["model_id"]
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context", "")
    clarification_answers = _format_clarification_answers(state)

    prompt = PRODUCT_GENERATION_PROMPT.format(
        analysis=analysis,
        rag_context=rag_context,
        clarification_answers=clarification_answers,
        **mem,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the Product configurations now."),
        ]
    )

    content = extract_llm_text(response.content)
    products = parse_entity_list(content)

    messages = state.get("messages", []) + [
        {"role": "assistant", "content": content, "step": "generate_products"}
    ]

    if not products:
        return {
            "products": [],
            "current_step": "error",
            "error": (
                "Failed to generate products — the AI model returned an"
                " invalid response. Please try again or select a different model."
            ),
            "messages": messages,
        }

    return {
        "products": products,
        "current_step": "products_generated",
        "messages": messages,
    }


async def generate_meters(state: WorkflowState, config: RunnableConfig) -> dict:
    """Generate Meter entity configurations using LLM.

    References previously approved Products for cross-linking.
    """
    mem = await load_generation_memory(config, state, "meter", from_store=True)

    model_id = state["model_id"]
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context", "")
    clarification_answers = _format_clarification_answers(state)
    products = state.get("products", [])

    prompt = METER_GENERATION_PROMPT.format(
        analysis=analysis,
        rag_context=rag_context,
        clarification_answers=clarification_answers,
        products=json.dumps(products, indent=2),
        **mem,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the Meter configurations now."),
        ]
    )

    content = extract_llm_text(response.content)
    meters = parse_entity_list(content)

    # Inject productId from approved products
    if meters and products:
        inject_parent_references(meters, "productId", products, code_hint_field="productCode")

    messages = state.get("messages", []) + [
        {"role": "assistant", "content": content, "step": "generate_meters"}
    ]

    if not meters:
        return {
            "meters": [],
            "current_step": "error",
            "error": (
                "Failed to generate meters — the AI model returned an"
                " invalid response. Please try again or select a different model."
            ),
            "messages": messages,
        }

    return {
        "meters": meters,
        "current_step": "meters_generated",
        "messages": messages,
    }


async def generate_aggregations(state: WorkflowState, config: RunnableConfig) -> dict:
    """Generate Aggregation entity configurations using LLM.

    References previously approved Products and Meters for cross-linking.
    """
    mem = await load_generation_memory(config, state, "aggregation", from_store=True)

    model_id = state["model_id"]
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context", "")
    clarification_answers = _format_clarification_answers(state)
    products = state.get("products", [])
    meters = state.get("meters", [])

    prompt = AGGREGATION_GENERATION_PROMPT.format(
        analysis=analysis,
        rag_context=rag_context,
        clarification_answers=clarification_answers,
        products=json.dumps(products, indent=2),
        meters=json.dumps(meters, indent=2),
        **mem,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the Aggregation configurations now."),
        ]
    )

    content = extract_llm_text(response.content)
    aggregations = parse_entity_list(content)

    # Inject meterId from approved meters
    if aggregations and meters:
        inject_parent_references(aggregations, "meterId", meters, code_hint_field="meterCode")

    messages = state.get("messages", []) + [
        {"role": "assistant", "content": content, "step": "generate_aggregations"}
    ]

    if not aggregations:
        return {
            "aggregations": [],
            "current_step": "error",
            "error": (
                "Failed to generate aggregations — the AI model returned an"
                " invalid response. Please try again or select a different model."
            ),
            "messages": messages,
        }

    return {
        "aggregations": aggregations,
        "current_step": "aggregations_generated",
        "messages": messages,
    }


async def generate_compound_aggregations(state: WorkflowState, config: RunnableConfig) -> dict:
    """Generate Compound Aggregation entity configurations using LLM.

    References previously approved aggregations for formula construction.
    """
    mem = await load_generation_memory(config, state, "compound_aggregation", from_store=True)

    model_id = state["model_id"]
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context", "")
    clarification_answers = _format_clarification_answers(state)
    products = state.get("products", [])
    aggregations = state.get("aggregations", [])

    prompt = COMPOUND_AGGREGATION_GENERATION_PROMPT.format(
        analysis=analysis,
        rag_context=rag_context,
        clarification_answers=clarification_answers,
        products=json.dumps(products, indent=2),
        aggregations=json.dumps(aggregations, indent=2),
        **mem,
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(
                content="Generate the Compound Aggregation configurations now. "
                "Return an empty array [] if none are needed."
            ),
        ]
    )

    content = extract_llm_text(response.content)
    compound_aggregations = parse_entity_list(content)

    # Inject productId from approved products
    if compound_aggregations and products:
        inject_parent_references(
            compound_aggregations, "productId", products, code_hint_field="productCode"
        )

    messages = state.get("messages", []) + [
        {"role": "assistant", "content": content, "step": "generate_compound_aggregations"}
    ]

    # Empty array is valid — not all use cases need compound aggregations
    if compound_aggregations is None:
        compound_aggregations = []

    return {
        "compound_aggregations": compound_aggregations,
        "current_step": "compound_aggregations_generated",
        "messages": messages,
    }
