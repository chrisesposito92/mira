"""WebSocket endpoint for real-time workflow streaming."""

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from app.agents.graphs.product_meter_agg import build_product_meter_agg_graph
from app.agents.utils import extract_interrupt_payload
from app.auth.jwt import verify_token
from app.db.client import get_supabase_client
from app.schemas.common import MessageRole, WorkflowStatus
from app.services.chat_message_service import save_message_internal

logger = logging.getLogger(__name__)

router = APIRouter()


async def _authenticate_ws(websocket: WebSocket) -> UUID | None:
    """Authenticate WebSocket via token query parameter."""
    token = websocket.query_params.get("token")
    if not token:
        return None
    try:
        payload = verify_token(token)
        return UUID(payload["sub"])
    except Exception:
        return None


async def _send_interrupt_if_pending(websocket: WebSocket, graph: object, config: dict) -> bool:
    """Check graph state for an interrupt and send it to the client. Returns True if found."""
    graph_state = await graph.aget_state(config)
    payload = extract_interrupt_payload(graph_state)
    if isinstance(payload, dict):
        await websocket.send_json(payload)
        return True
    return False


async def _invoke_and_send_result(
    websocket: WebSocket,
    graph: object,
    config: dict,
    invoke_arg: object,
    supabase: object,
    workflow_id: str,
) -> bool:
    """Invoke graph, persist state to DB, and send result to client.

    Returns True if the workflow is waiting for more input (interrupted).
    """
    try:
        await graph.ainvoke(invoke_arg, config=config)
    except GraphInterrupt:
        pass
    except Exception as exc:
        logger.exception("Graph error for workflow %s", workflow_id)
        now = datetime.now(UTC).isoformat()
        supabase.table("workflows").update(
            {"status": WorkflowStatus.failed, "error_message": str(exc), "updated_at": now}
        ).eq("id", workflow_id).execute()
        await websocket.send_json({"type": "error", "message": "Workflow failed"})
        save_message_internal(
            supabase,
            workflow_id,
            MessageRole.system,
            "Workflow failed",
            metadata={
                "error": str(exc),
                "payload": {"type": "error", "message": "Workflow failed"},
            },
        )
        return False

    # Check for interrupt
    graph_state = await graph.aget_state(config)
    payload = extract_interrupt_payload(graph_state)

    if isinstance(payload, dict):
        now = datetime.now(UTC).isoformat()
        supabase.table("workflows").update(
            {
                "status": WorkflowStatus.interrupted,
                "interrupt_payload": payload,
                "updated_at": now,
            }
        ).eq("id", workflow_id).execute()
        await websocket.send_json(payload)
        interrupt_type = payload.get("type", "interrupt")
        saved = save_message_internal(
            supabase,
            workflow_id,
            MessageRole.assistant,
            f"Waiting for user input: {interrupt_type}",
            metadata={"payload": payload},
        )
        if saved is None:
            logger.warning(
                "Interrupt payload for workflow %s not persisted — "
                "chat history will be incomplete on reconnect",
                workflow_id,
            )
        return True

    # Workflow completed
    now = datetime.now(UTC).isoformat()
    supabase.table("workflows").update(
        {
            "status": WorkflowStatus.completed,
            "interrupt_payload": None,
            "completed_at": now,
            "updated_at": now,
        }
    ).eq("id", workflow_id).execute()
    await websocket.send_json(
        {
            "type": "complete",
            "message": "Workflow completed successfully.",
        }
    )
    save_message_internal(
        supabase,
        workflow_id,
        MessageRole.assistant,
        "Workflow completed successfully.",
        metadata={"payload": {"type": "complete", "message": "Workflow completed successfully."}},
    )
    return False


@router.websocket("/ws/workflows/{workflow_id}")
async def workflow_ws(websocket: WebSocket, workflow_id: str) -> None:
    """WebSocket endpoint for real-time workflow interaction.

    Message protocol (JSON):
    Server → Client:
        {type: "status",        step: str, message: str}
        {type: "entities",      entity_type: str, entities: [...], errors: [...]}
        {type: "clarification", questions: [...]}
        {type: "complete",      message: str}
        {type: "error",         message: str}

    Client → Server:
        {type: "resume",  decisions: [...]}
        {type: "clarify", answers: [...]}
    """
    user_id = await _authenticate_ws(websocket)
    if not user_id:
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    # Verify workflow ownership via the service layer
    supabase = get_supabase_client()
    from app.services.workflow_service import get_workflow

    try:
        workflow = get_workflow(supabase, user_id, UUID(workflow_id))
    except Exception:
        await websocket.send_json({"type": "error", "message": "Workflow not found"})
        await websocket.close()
        return

    thread_id = workflow.get("thread_id")
    if not thread_id:
        await websocket.send_json({"type": "error", "message": "Workflow has no thread"})
        await websocket.close()
        return

    config = {"configurable": {"thread_id": thread_id}}

    try:
        graph = await build_product_meter_agg_graph()

        # Send current interrupt state if any
        await _send_interrupt_if_pending(websocket, graph, config)

        # Listen for client messages
        while True:
            try:
                raw = await websocket.receive_text()
                message = json.loads(raw)
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected for workflow %s", workflow_id)
                break
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = message.get("type")

            if msg_type == "resume":
                decisions_payload = {
                    "type": "user_decision",
                    "decisions": message.get("decisions", []),
                }
                save_message_internal(
                    supabase,
                    workflow_id,
                    MessageRole.user,
                    "Entity decisions submitted",
                    metadata={"payload": decisions_payload},
                )
                status_msg = {
                    "type": "status",
                    "step": "resuming",
                    "message": "Processing your decisions...",
                }
                await websocket.send_json(status_msg)
                save_message_internal(
                    supabase,
                    workflow_id,
                    MessageRole.assistant,
                    status_msg["message"],
                    metadata={"payload": status_msg},
                )
                now = datetime.now(UTC).isoformat()
                supabase.table("workflows").update(
                    {"status": WorkflowStatus.running, "updated_at": now}
                ).eq("id", workflow_id).execute()
                should_continue = await _invoke_and_send_result(
                    websocket,
                    graph,
                    config,
                    Command(resume=message.get("decisions", [])),
                    supabase,
                    workflow_id,
                )
                if not should_continue:
                    break

            elif msg_type == "clarify":
                clarify_payload = {
                    "type": "user_clarification",
                    "answers": message.get("answers", []),
                }
                save_message_internal(
                    supabase,
                    workflow_id,
                    MessageRole.user,
                    "Clarification answers submitted",
                    metadata={"payload": clarify_payload},
                )
                status_msg = {
                    "type": "status",
                    "step": "processing_clarification",
                    "message": "Processing your answers...",
                }
                await websocket.send_json(status_msg)
                save_message_internal(
                    supabase,
                    workflow_id,
                    MessageRole.assistant,
                    status_msg["message"],
                    metadata={"payload": status_msg},
                )
                now = datetime.now(UTC).isoformat()
                supabase.table("workflows").update(
                    {"status": WorkflowStatus.running, "updated_at": now}
                ).eq("id", workflow_id).execute()
                should_continue = await _invoke_and_send_result(
                    websocket,
                    graph,
                    config,
                    Command(resume=message.get("answers", [])),
                    supabase,
                    workflow_id,
                )
                if not should_continue:
                    break

            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                    }
                )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for workflow %s", workflow_id)
    except Exception:
        logger.exception("WebSocket error for workflow %s", workflow_id)
        try:
            await websocket.send_json({"type": "error", "message": "Internal server error"})
        except Exception:
            pass
