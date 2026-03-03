"""WebSocket endpoints for real-time workflow streaming, push progress,
document processing, and use case generation."""

import asyncio
import json
import logging
import uuid as uuid_mod
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langgraph.errors import GraphInterrupt
from langgraph.types import Command
from supabase import Client

from app.agents.utils import extract_interrupt_payload
from app.auth.jwt import verify_token
from app.db.client import get_supabase_client
from app.schemas.common import MessageRole, WorkflowStatus, WorkflowType
from app.services.chat_message_service import save_message_internal
from app.services.document_processing_registry import register_listener, unregister_listener
from app.services.workflow_service import get_graph

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

    # Check for error state (graph reached END with current_step == "error")
    final_values = graph_state.values if graph_state else {}
    if final_values.get("current_step") == "error":
        error_msg = final_values.get("error", "Workflow ended in error state")
        now = datetime.now(UTC).isoformat()
        supabase.table("workflows").update(
            {
                "status": WorkflowStatus.failed,
                "error_message": error_msg,
                "updated_at": now,
            }
        ).eq("id", workflow_id).execute()
        await websocket.send_json({"type": "error", "message": error_msg})
        save_message_internal(
            supabase,
            workflow_id,
            MessageRole.system,
            error_msg,
            metadata={"payload": {"type": "error", "message": error_msg}},
        )
        return False

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

    try:
        wf_type = workflow.get("workflow_type", WorkflowType.product_meter_aggregation)
        config = {
            "configurable": {"thread_id": thread_id},
            "run_name": f"mira-{wf_type}",
            "metadata": {
                "workflow_id": workflow_id,
                "workflow_type": wf_type,
                "source": "websocket",
            },
            "tags": ["mira", wf_type, "websocket"],
        }
        graph = await get_graph(wf_type)

        # Send current interrupt state if any
        has_interrupt = await _send_interrupt_if_pending(websocket, graph, config)

        # If the workflow already finished (failed/completed via REST before WS connected),
        # send the terminal message immediately and close — don't enter the message loop.
        if not has_interrupt:
            wf_status = workflow.get("status")
            if wf_status == WorkflowStatus.failed:
                error_msg = workflow.get("error_message", "Workflow failed")
                await websocket.send_json({"type": "error", "message": error_msg})
                # Don't persist — the error message was already saved when
                # the workflow was marked failed.  Re-saving on each reconnect
                # would create duplicates in chat history.
                await websocket.close()
                return
            if wf_status == WorkflowStatus.completed:
                await websocket.send_json(
                    {"type": "complete", "message": "Workflow completed successfully."}
                )
                await websocket.close()
                return

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


@router.websocket("/ws/push/{use_case_id}")
async def push_ws(websocket: WebSocket, use_case_id: str) -> None:
    """WebSocket endpoint for real-time push progress.

    Message protocol (JSON):
    Client → Server:
        {type: "start_push", object_ids: [...] | null}

    Server → Client:
        {type: "push_started", total: N}
        {type: "push_progress", entity_id: str, entity_type: str, success: bool,
         m3ter_id: str|null, error: str|null, completed: N, total: N}
        {type: "push_complete", total: N, succeeded: N, failed: N, skipped: N}
        {type: "push_error", message: str}
    """
    user_id = await _authenticate_ws(websocket)
    if not user_id:
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    # Verify use case ownership
    supabase = get_supabase_client()
    uc_result = (
        supabase.table("use_cases")
        .select("id, projects!inner(user_id)")
        .eq("id", use_case_id)
        .execute()
    )
    if not uc_result.data:
        await websocket.send_json({"type": "push_error", "message": "Use case not found"})
        await websocket.close()
        return

    uc_owner = uc_result.data[0].get("projects", {}).get("user_id")
    if uc_owner != str(user_id):
        await websocket.send_json({"type": "push_error", "message": "Use case not found"})
        await websocket.close()
        return

    try:
        # Wait for start_push message
        raw = await websocket.receive_text()
        message = json.loads(raw)

        if message.get("type") != "start_push":
            await websocket.send_json(
                {"type": "push_error", "message": f"Expected start_push, got {message.get('type')}"}
            )
            await websocket.close()
            return

        raw_ids = message.get("object_ids")
        object_ids = [UUID(oid) for oid in raw_ids] if raw_ids is not None else None

        from app.services.push_service import push_use_case_objects

        # Count eligible objects first to send push_started before the push begins
        eligible_result = (
            supabase.table("generated_objects")
            .select("id, status")
            .eq("use_case_id", use_case_id)
            .in_("status", ["approved", "push_failed"])
            .execute()
        )
        eligible_objects = eligible_result.data or []
        if object_ids is not None:
            str_ids = {str(oid) for oid in object_ids}
            eligible_objects = [o for o in eligible_objects if o["id"] in str_ids]
        total = len(eligible_objects)

        await websocket.send_json({"type": "push_started", "total": total})

        completed_count = 0
        # Track already-pushed entity IDs so we don't count them toward progress.
        # These are included by the push engine for reference resolution but aren't
        # part of the eligible set — query them separately since eligible_objects
        # only contains approved/push_failed rows.
        pushed_result = (
            supabase.table("generated_objects")
            .select("id")
            .eq("use_case_id", use_case_id)
            .eq("status", "pushed")
            .execute()
        )
        already_pushed_ids = {o["id"] for o in (pushed_result.data or [])}

        async def on_progress(result):
            """Async callback to stream progress via WebSocket in real-time."""
            nonlocal completed_count
            # Skip already-pushed objects (included only for reference resolution)
            if result.entity_id in already_pushed_ids:
                return
            completed_count += 1
            try:
                await websocket.send_json(
                    {
                        "type": "push_progress",
                        "entity_id": result.entity_id,
                        "entity_type": result.entity_type,
                        "success": result.success,
                        "m3ter_id": result.m3ter_id,
                        "error": result.error,
                        "completed": completed_count,
                        "total": total,
                    }
                )
            except Exception:
                logger.warning("Failed to send push progress for %s", result.entity_id)

        bulk_result = await push_use_case_objects(
            supabase, user_id, UUID(use_case_id), object_ids, on_progress
        )

        await websocket.send_json(
            {
                "type": "push_complete",
                "total": total,
                "succeeded": bulk_result.succeeded,
                "failed": bulk_result.failed,
                "skipped": bulk_result.skipped,
            }
        )

    except WebSocketDisconnect:
        logger.info("Push WebSocket disconnected for use case %s", use_case_id)
    except Exception as exc:
        logger.exception("Push WebSocket error for use case %s", use_case_id)
        try:
            await websocket.send_json({"type": "push_error", "message": str(exc)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


async def _verify_project_ws(
    websocket: WebSocket, supabase: Client, project_id: str, user_id: UUID, error_type: str
) -> bool:
    """Verify project ownership for a WebSocket connection.

    Sends an error and closes the socket if verification fails.
    Returns True if ownership is verified.
    """
    project_result = supabase.table("projects").select("id, user_id").eq("id", project_id).execute()
    if not project_result.data:
        await websocket.send_json({"type": error_type, "message": "Project not found"})
        await websocket.close()
        return False

    project_owner = project_result.data[0].get("user_id")
    if project_owner != str(user_id):
        await websocket.send_json({"type": error_type, "message": "Project not found"})
        await websocket.close()
        return False

    return True


@router.websocket("/ws/documents/{project_id}")
async def document_ws(websocket: WebSocket, project_id: str) -> None:
    """WebSocket endpoint for real-time document processing progress.

    Passive observer — no client-to-server messages expected.

    Server → Client:
        {type: "doc_processing_started",  document_id, filename, stage}
        {type: "doc_processing_progress", document_id, stage, detail?}
        {type: "doc_processing_complete", document_id, chunk_count}
        {type: "doc_processing_error",    document_id, error}
    """
    user_id = await _authenticate_ws(websocket)
    if not user_id:
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    supabase = get_supabase_client()
    if not await _verify_project_ws(websocket, supabase, project_id, user_id, "error"):
        return

    register_listener(project_id, websocket)

    try:
        while True:
            try:
                # Keep alive — wait for client messages or detect disconnect.
                # We use wait_for with a timeout to periodically send pings,
                # which detects stale connections.
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except TimeoutError:
                # Send a ping to keep the connection alive and detect staleness
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Document WebSocket error for project %s", project_id)
    finally:
        unregister_listener(project_id, websocket)
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/ws/generate/{project_id}")
async def generate_ws(websocket: WebSocket, project_id: str) -> None:
    """WebSocket endpoint for use case generation.

    Client -> Server:
        {type: "start_generate", customer_name, num_use_cases, notes?, attachment_text?, model_id}
        {type: "clarify", answers: [...]}

    Server -> Client:
        {type: "gen_status",        step, message}
        {type: "gen_clarification", questions: [...]}
        {type: "gen_use_cases",     use_cases: [...]}
        {type: "gen_error",         message}
    """
    user_id = await _authenticate_ws(websocket)
    if not user_id:
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    supabase = get_supabase_client()
    if not await _verify_project_ws(websocket, supabase, project_id, user_id, "gen_error"):
        return

    thread_id: str | None = None
    try:
        # Wait for start_generate message
        raw = await websocket.receive_text()
        message = json.loads(raw)

        if message.get("type") != "start_generate":
            await websocket.send_json(
                {
                    "type": "gen_error",
                    "message": f"Expected start_generate, got {message.get('type')}",
                }
            )
            await websocket.close()
            return

        # Validate required fields
        customer_name = message.get("customer_name")
        model_id = message.get("model_id")
        if not customer_name or not model_id:
            await websocket.send_json(
                {"type": "gen_error", "message": "customer_name and model_id are required"}
            )
            await websocket.close()
            return

        # Validate and clamp num_use_cases to 1-10
        raw_num = message.get("num_use_cases", 1)
        num_use_cases = max(1, min(10, int(raw_num))) if isinstance(raw_num, (int, float)) else 1

        # Truncate attachment_text to ~50K chars to avoid overflowing LLM context
        max_attachment_chars = 50_000
        attachment_text = message.get("attachment_text", "")
        if len(attachment_text) > max_attachment_chars:
            attachment_text = attachment_text[:max_attachment_chars] + "\n\n[Truncated]"

        from app.agents.graphs.use_case_gen import build_use_case_gen_graph

        thread_id = str(uuid_mod.uuid4())
        config = {
            "configurable": {"thread_id": thread_id},
            "run_name": "mira-use-case-generator",
            "metadata": {
                "project_id": project_id,
                "customer_name": customer_name,
                "model_id": model_id,
                "source": "websocket",
            },
            "tags": ["mira", "use_case_gen", "websocket"],
        }

        graph = await build_use_case_gen_graph()

        initial_state = {
            "project_id": project_id,
            "customer_name": customer_name,
            "num_use_cases": num_use_cases,
            "notes": message.get("notes", ""),
            "attachment_text": attachment_text,
            "model_id": model_id,
            "user_id": str(user_id),
            "thread_id": thread_id,
            "current_step": "starting",
        }

        await websocket.send_json(
            {"type": "gen_status", "step": "researching", "message": "Researching company..."}
        )

        # Run graph — always check state for interrupts (LangGraph 1.x
        # returns normally on interrupt instead of raising GraphInterrupt).
        try:
            result = await graph.ainvoke(initial_state, config=config)
        except GraphInterrupt:
            result = None

        graph_state = await graph.aget_state(config)
        interrupt_payload = extract_interrupt_payload(graph_state)

        is_clarification = (
            isinstance(interrupt_payload, dict)
            and interrupt_payload.get("type") == "gen_clarification"
        )
        if is_clarification:
            await websocket.send_json(interrupt_payload)

            # Wait for clarify response
            while True:
                try:
                    raw = await websocket.receive_text()
                    msg = json.loads(raw)
                except WebSocketDisconnect:
                    return
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "gen_error", "message": "Invalid JSON"})
                    continue

                if msg.get("type") == "clarify":
                    answers = msg.get("answers", [])
                    await websocket.send_json(
                        {
                            "type": "gen_status",
                            "step": "compiling",
                            "message": "Generating use cases...",
                        }
                    )

                    try:
                        result = await graph.ainvoke(Command(resume=answers), config=config)
                    except GraphInterrupt:
                        result = None

                    break
                else:
                    await websocket.send_json(
                        {
                            "type": "gen_error",
                            "message": f"Expected clarify, got {msg.get('type')}",
                        }
                    )

        # Always read final state from the graph (LangGraph 1.x returns the
        # state dict from ainvoke, but reading via aget_state is authoritative).
        final_state = await graph.aget_state(config)
        final_values = final_state.values if hasattr(final_state, "values") else {}
        if result is None:
            result = final_values

        generated = result.get("generated_use_cases", []) or final_values.get(
            "generated_use_cases", []
        )
        if generated:
            await websocket.send_json({"type": "gen_use_cases", "use_cases": generated})
        else:
            await websocket.send_json(
                {"type": "gen_error", "message": "No use cases were generated."}
            )

    except WebSocketDisconnect:
        logger.info("Generator WebSocket disconnected for project %s", project_id)
    except Exception as exc:
        logger.exception("Generator WebSocket error for project %s", project_id)
        try:
            await websocket.send_json({"type": "gen_error", "message": str(exc)})
        except Exception:
            pass
    finally:
        # Clean up question cache to prevent memory leak on disconnect
        if thread_id:
            from app.agents.nodes.use_case_clarify import cleanup_question_cache

            cleanup_question_cache(thread_id)
        try:
            await websocket.close()
        except Exception:
            pass
