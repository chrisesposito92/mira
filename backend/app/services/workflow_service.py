"""Service layer for workflows — read operations + LangGraph start/resume."""

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from langgraph.errors import GraphInterrupt
from langgraph.types import Command
from supabase import Client

from app.agents.graphs.product_meter_agg import build_product_meter_agg_graph
from app.agents.utils import extract_interrupt_payload
from app.schemas.common import WorkflowStatus, WorkflowType

logger = logging.getLogger(__name__)


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
    graph: object,
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

    return _update_workflow(
        supabase,
        workflow_id,
        {
            "status": WorkflowStatus.completed,
            "interrupt_payload": None,
            "completed_at": datetime.now(UTC).isoformat(),
        },
    )


async def start_workflow(supabase: Client, user_id: UUID, use_case_id: UUID, model_id: str) -> dict:
    """Start a new product/meter/aggregation workflow for a use case."""
    use_case = _verify_use_case_ownership(supabase, user_id, use_case_id)
    project_id = use_case.get("project_id", "")

    workflow_id = str(uuid4())
    thread_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    supabase.table("workflows").insert(
        {
            "id": workflow_id,
            "use_case_id": str(use_case_id),
            "workflow_type": WorkflowType.product_meter_aggregation,
            "status": WorkflowStatus.running,
            "thread_id": thread_id,
            "started_at": now,
            "created_at": now,
            "updated_at": now,
        }
    ).execute()

    graph = await build_product_meter_agg_graph()
    initial_state = {
        "use_case_id": str(use_case_id),
        "project_id": str(project_id),
        "model_id": model_id,
        "user_id": str(user_id),
    }
    config = {"configurable": {"thread_id": thread_id}}

    return await _invoke_and_handle(graph, config, initial_state, supabase, workflow_id)


async def resume_workflow(
    supabase: Client, user_id: UUID, workflow_id: UUID, decisions: list[dict]
) -> dict:
    """Resume a workflow after user approval/edit/reject decisions."""
    workflow = get_workflow(supabase, user_id, workflow_id)
    if workflow["status"] != WorkflowStatus.interrupted:
        raise HTTPException(status_code=400, detail="Workflow is not in interrupted state")

    thread_id = workflow["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}
    wf_id = str(workflow_id)

    _update_workflow(supabase, wf_id, {"status": WorkflowStatus.running})

    graph = await build_product_meter_agg_graph()
    return await _invoke_and_handle(graph, config, Command(resume=decisions), supabase, wf_id)


async def resume_workflow_clarification(
    supabase: Client, user_id: UUID, workflow_id: UUID, answers: list[dict]
) -> dict:
    """Resume a workflow after user answers clarification questions."""
    return await resume_workflow(supabase, user_id, workflow_id, answers)
