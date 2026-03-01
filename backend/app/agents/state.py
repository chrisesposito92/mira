"""LangGraph workflow state definition for all agent workflows (WF1–WF4)."""

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

    # Workflow 1 — Generation (batches of entity dicts)
    products: list[dict]
    meters: list[dict]
    aggregations: list[dict]

    # Workflow 1 — Validation
    product_errors: list[dict]  # [{entity_index, errors: [...]}]
    meter_errors: list[dict]
    aggregation_errors: list[dict]

    # Workflow 1 — Approval decisions from user (via Command(resume=...))
    product_decisions: list[dict]  # [{index, action, data?}]
    meter_decisions: list[dict]
    aggregation_decisions: list[dict]

    # Workflow 2 — loaded from DB (approved entities from Workflow 1)
    approved_products: list[dict]
    approved_meters: list[dict]
    approved_aggregations: list[dict]

    # Workflow 2 — Generation
    plan_templates: list[dict]
    plans: list[dict]
    pricing: list[dict]

    # Workflow 2 — Validation
    plan_template_errors: list[dict]
    plan_errors: list[dict]
    pricing_errors: list[dict]

    # Workflow 2 — Approval decisions
    plan_template_decisions: list[dict]
    plan_decisions: list[dict]
    pricing_decisions: list[dict]

    # Workflow 3 — loaded from DB (approved entities from Workflow 1 + Workflow 2)
    approved_plan_templates: list[dict]
    approved_plans: list[dict]
    approved_pricing: list[dict]

    # Workflow 3 — Generation
    accounts: list[dict]
    account_plans: list[dict]

    # Workflow 3 — Validation
    account_errors: list[dict]
    account_plan_errors: list[dict]

    # Workflow 3 — Approval decisions
    account_decisions: list[dict]
    account_plan_decisions: list[dict]

    # Workflow 4 — loaded from DB (approved meters from WF1, approved accounts from WF3)
    approved_accounts: list[dict]

    # Workflow 4 — Generation
    measurements: list[dict]

    # Workflow 4 — Validation
    measurement_errors: list[dict]

    # Workflow 4 — Approval decisions
    measurement_decisions: list[dict]

    # Tracking
    thread_id: str  # LangGraph thread_id — unique per workflow run
    messages: list[dict]  # chat-style message log
    current_step: str  # for progress tracking
    error: str | None  # terminal error
