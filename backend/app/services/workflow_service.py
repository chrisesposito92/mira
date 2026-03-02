"""Service layer for workflows — read operations + LangGraph start/resume."""

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from langgraph.errors import GraphInterrupt
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from supabase import Client

from app.agents.graphs.account_setup import build_account_setup_graph
from app.agents.graphs.plan_pricing import build_plan_pricing_graph
from app.agents.graphs.product_meter_agg import build_product_meter_agg_graph
from app.agents.graphs.usage_submission import build_usage_submission_graph
from app.agents.utils import extract_interrupt_payload
from app.schemas.common import WorkflowStatus, WorkflowType

logger = logging.getLogger(__name__)


_SUPPORTED_WORKFLOW_TYPES = {
    WorkflowType.product_meter_aggregation,
    WorkflowType.plan_pricing,
    WorkflowType.account_setup,
    WorkflowType.usage_submission,
}


async def get_graph(workflow_type: WorkflowType) -> CompiledStateGraph:
    """Build the correct LangGraph graph for the given workflow type."""
    if workflow_type == WorkflowType.product_meter_aggregation:
        return await build_product_meter_agg_graph()
    if workflow_type == WorkflowType.plan_pricing:
        return await build_plan_pricing_graph()
    if workflow_type == WorkflowType.account_setup:
        return await build_account_setup_graph()
    if workflow_type == WorkflowType.usage_submission:
        return await build_usage_submission_graph()
    raise ValueError(f"Unsupported workflow type: {workflow_type}")


def list_workflows(supabase: Client, user_id: UUID, use_case_id: UUID) -> list[dict]:
    _verify_use_case_ownership(supabase, user_id, use_case_id)
    result = (
        supabase.table("workflows")
        .select("*")
        .eq("use_case_id", str(use_case_id))
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_workflow(supabase: Client, user_id: UUID, workflow_id: UUID) -> dict:
    result = (
        supabase.table("workflows")
        .select("*, use_cases!inner(project_id, projects!inner(user_id))")
        .eq("id", str(workflow_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    row = result.data[0]
    project_user_id = row.get("use_cases", {}).get("projects", {}).get("user_id")
    if project_user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {k: v for k, v in row.items() if k != "use_cases"}


def _verify_use_case_ownership(supabase: Client, user_id: UUID, use_case_id: UUID) -> dict:
    """Fetch use case with ownership check. Returns the full use case row."""
    result = (
        supabase.table("use_cases")
        .select("*, projects!inner(user_id)")
        .eq("id", str(use_case_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Use case not found")
    row = result.data[0]
    if row.get("projects", {}).get("user_id") != str(user_id):
        raise HTTPException(status_code=404, detail="Use case not found")
    return row


def _update_workflow(supabase: Client, workflow_id: str, fields: dict) -> dict:
    """Update a workflow row and return the updated data."""
    fields["updated_at"] = datetime.now(UTC).isoformat()
    result = supabase.table("workflows").update(fields).eq("id", workflow_id).execute()
    return result.data[0] if result.data else {}


async def _invoke_and_handle(
    graph: CompiledStateGraph,
    config: dict,
    invoke_arg: object,
    supabase: Client,
    workflow_id: str,
) -> dict:
    """Invoke the graph and handle interrupt vs completion.

    Returns the updated workflow row dict.
    """
    try:
        await graph.ainvoke(invoke_arg, config=config)
    except GraphInterrupt:
        graph_state = await graph.aget_state(config)
        interrupt_payload = extract_interrupt_payload(graph_state)
        return _update_workflow(
            supabase,
            workflow_id,
            {
                "status": WorkflowStatus.interrupted,
                "interrupt_payload": interrupt_payload,
            },
        )
    except Exception as exc:
        logger.exception("Graph invocation failed for workflow %s", workflow_id)
        return _update_workflow(
            supabase,
            workflow_id,
            {
                "status": WorkflowStatus.failed,
                "error_message": str(exc),
            },
        )

    # Check if the graph ended in an error state (e.g., load node returned error
    # and the graph routed to END). This must be marked as failed, not completed,
    # to prevent downstream workflows from incorrectly satisfying prerequisite checks.
    graph_state = await graph.aget_state(config)
    final_values = graph_state.values if graph_state else {}
    if final_values.get("current_step") == "error":
        error_msg = final_values.get("error", "Workflow ended in error state")
        return _update_workflow(
            supabase,
            workflow_id,
            {
                "status": WorkflowStatus.failed,
                "error_message": error_msg,
            },
        )

    return _update_workflow(
        supabase,
        workflow_id,
        {
            "status": WorkflowStatus.completed,
            "interrupt_payload": None,
            "completed_at": datetime.now(UTC).isoformat(),
        },
    )


async def start_workflow(
    supabase: Client,
    user_id: UUID,
    use_case_id: UUID,
    model_id: str,
    workflow_type: WorkflowType = WorkflowType.product_meter_aggregation,
) -> dict:
    """Start a new workflow for a use case."""
    if workflow_type not in _SUPPORTED_WORKFLOW_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported workflow type: {workflow_type}",
        )

    use_case = _verify_use_case_ownership(supabase, user_id, use_case_id)
    project_id = use_case.get("project_id", "")

    # Prerequisite checks: each workflow requires its predecessor to be completed
    prerequisites: dict[WorkflowType, tuple[WorkflowType, str]] = {
        WorkflowType.plan_pricing: (
            WorkflowType.product_meter_aggregation,
            "Workflow 1 (Products, Meters & Aggregations) must be completed first",
        ),
        WorkflowType.account_setup: (
            WorkflowType.plan_pricing,
            "Workflow 2 (Plans & Pricing) must be completed first",
        ),
        WorkflowType.usage_submission: (
            WorkflowType.account_setup,
            "Workflow 3 (Account Setup) must be completed first",
        ),
    }

    prereq = prerequisites.get(workflow_type)
    if prereq:
        required_type, error_msg = prereq
        prereq_check = (
            supabase.table("workflows")
            .select("id")
            .eq("use_case_id", str(use_case_id))
            .eq("workflow_type", required_type)
            .eq("status", WorkflowStatus.completed)
            .limit(1)
            .execute()
        )
        if not prereq_check.data:
            raise HTTPException(status_code=400, detail=error_msg)

    workflow_id = str(uuid4())
    thread_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    supabase.table("workflows").insert(
        {
            "id": workflow_id,
            "use_case_id": str(use_case_id),
            "workflow_type": workflow_type,
            "status": WorkflowStatus.running,
            "thread_id": thread_id,
            "model_id": model_id,
            "started_at": now,
            "created_at": now,
            "updated_at": now,
        }
    ).execute()

    try:
        graph = await get_graph(workflow_type)

        initial_state = {
            "use_case_id": str(use_case_id),
            "project_id": str(project_id),
            "model_id": model_id,
            "user_id": str(user_id),
            "thread_id": thread_id,
        }
        config = {
            "configurable": {"thread_id": thread_id},
            "run_name": f"mira-{workflow_type}",
            "metadata": {
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "use_case_id": str(use_case_id),
                "model_id": model_id,
                "source": "rest",
            },
            "tags": ["mira", workflow_type, "start"],
        }

        return await _invoke_and_handle(graph, config, initial_state, supabase, workflow_id)
    except Exception as exc:
        logger.exception("Failed to build or invoke graph for workflow %s", workflow_id)
        _update_workflow(
            supabase,
            workflow_id,
            {
                "status": WorkflowStatus.failed,
                "error_message": str(exc),
            },
        )
        raise HTTPException(status_code=500, detail="Workflow failed to start") from exc


async def resume_workflow(
    supabase: Client, user_id: UUID, workflow_id: UUID, decisions: list[dict]
) -> dict:
    """Resume a workflow after user approval/edit/reject decisions."""
    workflow = get_workflow(supabase, user_id, workflow_id)
    if workflow["status"] != WorkflowStatus.interrupted:
        raise HTTPException(status_code=400, detail="Workflow is not in interrupted state")

    thread_id = workflow["thread_id"]
    wf_id = str(workflow_id)
    wf_type = workflow.get("workflow_type", WorkflowType.product_meter_aggregation)

    config = {
        "configurable": {"thread_id": thread_id},
        "run_name": f"mira-{wf_type}",
        "metadata": {
            "workflow_id": wf_id,
            "workflow_type": wf_type,
            "use_case_id": workflow.get("use_case_id", ""),
            "source": "rest",
        },
        "tags": ["mira", wf_type, "resume"],
    }

    _update_workflow(supabase, wf_id, {"status": WorkflowStatus.running})

    graph = await get_graph(wf_type)
    return await _invoke_and_handle(graph, config, Command(resume=decisions), supabase, wf_id)


async def resume_workflow_clarification(
    supabase: Client, user_id: UUID, workflow_id: UUID, answers: list[dict]
) -> dict:
    """Resume a workflow after user answers clarification questions."""
    return await resume_workflow(supabase, user_id, workflow_id, answers)
