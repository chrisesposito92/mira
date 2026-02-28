"""LangGraph workflow state definition for product/meter/aggregation agent."""

from typing import TypedDict


class WorkflowState(TypedDict, total=False):
    # Input
    use_case_id: str
    use_case: dict  # fetched use case data
    project_id: str  # for RAG project scoping
    model_id: str  # selected LLM model
    user_id: str  # owner

    # Analysis
    analysis: str  # LLM analysis of the use case
    rag_context: str  # assembled RAG chunks

    # Clarification
    needs_clarification: bool
    clarification_questions: list[dict]  # [{question, options, recommendation}]
    clarification_answers: list[dict]  # user responses from resume

    # Generation — batches of entity dicts
    products: list[dict]
    meters: list[dict]
    aggregations: list[dict]

    # Validation
    product_errors: list[dict]  # [{entity_index, errors: [...]}]
    meter_errors: list[dict]
    aggregation_errors: list[dict]

    # Approval decisions from user (via Command(resume=...))
    product_decisions: list[dict]  # [{index, action, data?}]
    meter_decisions: list[dict]
    aggregation_decisions: list[dict]

    # Tracking
    messages: list[dict]  # chat-style message log
    current_step: str  # for progress tracking
    error: str | None  # terminal error
