# Architecture

**Analysis Date:** 2026-03-22

## Pattern Overview

**Overall:** AI-orchestrated agent pipeline with human-in-the-loop (HITL) approval gates

**Key Characteristics:**
- Monorepo: FastAPI backend (Python) + SvelteKit frontend (TypeScript) + JSON shared constants
- Four sequential LangGraph `StateGraph` workflows (WF1→WF2→WF3→WF4), each producing m3ter billing entity types; each workflow gates on its predecessor completing
- Real-time bidirectional WebSocket layer (`ws.py`) drives the HITL interrupt/resume cycle alongside optional REST polling
- Long-term memory via `AsyncPostgresStore` (4 namespaces) enriches generation context across workflow runs; short-term state checkpointed via `AsyncPostgresSaver`
- Supabase (PostgreSQL + Auth + Storage) is the single source of truth for all persistent data; the backend uses service-role key (bypasses RLS) with ownership checks in service layer

## Layers

**API Layer:**
- Purpose: Receive HTTP/WebSocket requests, enforce auth, delegate to service layer
- Location: `backend/app/api/`
- Contains: `router.py` (aggregates all sub-routers), 10 route modules (`projects.py`, `use_cases.py`, `workflows.py`, `ws.py`, `generated_objects.py`, `documents.py`, `org_connections.py`, `chat_messages.py`, `m3ter_sync.py`, `use_case_generator.py`)
- Depends on: `app.dependencies` (auth DI), `app.services.*`, `app.schemas.*`
- Used by: External clients (SvelteKit frontend, API consumers)

**Dependency Injection:**
- Purpose: Provide auth-verified user_id and Supabase client to route handlers
- Location: `backend/app/dependencies.py`
- Contains: `get_current_user()` (Bearer JWT → UUID), `get_supabase()` (Supabase service-role client)
- Depends on: `app.auth.jwt.verify_token`, `app.db.client`
- Used by: All API route handlers via `Depends()`

**Service Layer:**
- Purpose: Business logic, ownership verification, orchestration; decoupled from HTTP concerns
- Location: `backend/app/services/`
- Contains: `workflow_service.py` (graph start/resume/get), `push_service.py` (m3ter entity push orchestration), `generated_object_service.py`, `project_service.py`, `use_case_service.py`, `document_service.py`, `document_processor.py`, `chat_message_service.py`, `org_connection_service.py`, `document_processing_registry.py`
- Depends on: `app.db.client`, `app.m3ter.*`, `app.rag.*`, `app.agents.graphs.*`
- Used by: API layer

**Agent / Workflow Layer:**
- Purpose: LangGraph StateGraph definitions, nodes, prompts, memory, LLM factory
- Location: `backend/app/agents/`
- Contains: `graphs/` (4 workflow graphs + use case generator graph), `nodes/` (14 node modules), `prompts/` (3 prompt modules), `tools/` (RAG tool, m3ter schema), `state.py` (WorkflowState + UseCaseGenState TypedDicts), `llm_factory.py` (6-model registry), `checkpointer.py` (AsyncPostgresSaver + AsyncPostgresStore), `memory.py`, `memory_decisions.py`, `memory_rag.py`, `utils.py`
- Depends on: `app.db.client`, `app.rag.*`, `app.validation.*`, `app.schemas.*`, LangChain/LangGraph
- Used by: `workflow_service.py`, `ws.py`

**Validation Layer:**
- Purpose: Per-entity rule enforcement before user approval; also used by object creation endpoint
- Location: `backend/app/validation/`
- Contains: `engine.py` (`validate_entity()` dispatcher), `common.py` (shared helpers), `cross_entity.py` (referential integrity), `rules/` (10 per-entity modules: `product.py`, `meter.py`, `aggregation.py`, `compound_aggregation.py`, `plan_template.py`, `plan.py`, `pricing.py`, `account.py`, `account_plan.py`, `measurement.py`)
- Depends on: `app.schemas.common`
- Used by: `nodes/validation.py`, `api/generated_objects.py`

**m3ter Integration Layer:**
- Purpose: OAuth2 client, reference resolution, payload mapping, ordered entity push
- Location: `backend/app/m3ter/`
- Contains: `client.py` (M3terClient — HTTP Basic auth token endpoint, class-level token cache 4h50m, retry logic 429/500/50x), `mapper.py` (allowlist-based MIRA→m3ter payload transformation), `entities.py` (PUSH_ORDER list, ReferenceResolver, `push_entities_ordered()`), `encryption.py` (Fernet credential encryption)
- Depends on: `app.schemas.common`, `app.agents.tools.m3ter_schema`
- Used by: `push_service.py`

**RAG Layer:**
- Purpose: Text chunking, OpenAI embeddings, pgvector ingestion, two-source retrieval
- Location: `backend/app/rag/`
- Contains: `chunker.py`, `embeddings.py` (batch OpenAI embedding via `text-embedding-3-small`), `ingestion.py`, `retriever.py` (two-source cosine similarity: `m3ter_docs` + project-scoped `user_document`)
- Depends on: `app.db.client` (asyncpg pool), `app.config`
- Used by: `agents/tools/rag_tool.py`, `services/document_service.py`

**Database Layer:**
- Purpose: Connection pool management and Supabase client singletons
- Location: `backend/app/db/`
- Contains: `client.py` (module-level singletons: `_supabase_client` service-role, `_supabase_anon_client`, `_db_pool` asyncpg)
- Depends on: `app.config`
- Used by: All layers that need DB access

**Auth Layer:**
- Purpose: JWT verification (Supabase-issued tokens)
- Location: `backend/app/auth/`
- Contains: `jwt.py` (Supabase JWT verification, `AuthError` exception), middleware wired in `main.py`
- Depends on: `app.config` (JWT secret)
- Used by: `app.dependencies`, `ws.py` (WebSocket token auth via query param)

**Schemas Layer:**
- Purpose: Pydantic v2 request/response models and shared StrEnums
- Location: `backend/app/schemas/`
- Contains: `common.py` (`EntityType`, `ObjectStatus`, `WorkflowType`, `WorkflowStatus`, `UseCaseStatus`, `MessageRole`, `BillingFrequency`, `ConnectionStatus`, `DocumentStatus`), plus per-domain schema files
- Depends on: pydantic
- Used by: All layers

**Frontend Stores:**
- Purpose: Svelte 5 runes-based client state management (class-based singletons)
- Location: `frontend/src/lib/stores/`
- Contains: `workflow.svelte.ts` (WorkflowStore — WS connection, messages, pending HITL interactions), `objects.svelte.ts` (ObjectsStore — generated object list, filtering, push session), `project.svelte.ts`, `auth.svelte.ts`, `org-connections.svelte.ts`
- Depends on: `$lib/services/*`, `$lib/types`
- Used by: SvelteKit route components

**Frontend Services:**
- Purpose: HTTP/WebSocket API client wrappers (factory functions)
- Location: `frontend/src/lib/services/`
- Contains: `api.ts` (base ApiClient), `workflow.ts` (`createWorkflowService()`), `generated-objects.ts` (`createGeneratedObjectService()`), `websocket.ts` (WebSocketClient with exponential backoff), `push-websocket.ts`, `doc-websocket.ts`, `generator-websocket.ts`, `projects.ts`, `use-cases.ts`, `documents.ts`, `org-connections.ts`
- Depends on: Supabase auth for JWT token injection
- Used by: Stores, route page components

## Data Flow

**Workflow Execution (WebSocket path):**

1. User selects workflow type + LLM model in `WorkflowLauncherDropdown.svelte`; `POST /api/use-cases/{id}/workflows/start` creates a workflow row (status: running) and invokes `graph.ainvoke(initial_state)` synchronously
2. Graph runs `analyze_use_case` (fetches use case from DB, calls RAG retriever, runs LLM) → may branch to `generate_clarifications` if LLM signals `needs_clarification`
3. Graph interrupts on first `approve_*` node via `interrupt(payload)` — payload written to `workflows.interrupt_payload` in DB; workflow status set to `interrupted`
4. Frontend `WorkflowStore` connects via `WebSocketClient` to `ws://host/ws/workflows/{id}`; server sends the interrupt payload immediately on connect
5. User reviews/edits/approves entities in `EntityCard.svelte`; store accumulates `EntityDecision[]` and sends `{type: "resume", decisions: [...]}` over WebSocket
6. `ws.py` calls `graph.ainvoke(Command(resume=decisions), config)` → graph re-executes `approve_entities` from the interrupt point, persists decisions to `generated_objects`, advances to next generate→validate→approve cycle
7. Steps 4-6 repeat for each entity type in the workflow; on final approval the graph reaches END, workflow status set to `completed`

**m3ter Push Flow:**

1. User selects approved objects in ObjectTree and clicks "Push Selected" → `PushConfirmDialog` shown
2. Frontend `PushWebSocketClient` connects to `ws://host/ws/push/{use_case_id}` and sends `{type: "start_push", object_ids: [...]}`
3. `push_ws` calls `push_use_case_objects()` from `push_service.py` → resolves org credentials → calls `push_entities_ordered()` in `m3ter/entities.py`
4. Push engine sorts entities by `PUSH_ORDER`, resolves MIRA UUIDs to m3ter UUIDs via `ReferenceResolver`, maps payloads via `mapper.py`, calls `M3terClient` create methods
5. Per-entity `on_progress` async callback streams `push_progress` messages over WebSocket; `PushProgressPanel.svelte` renders real-time status
6. DB updated: `generated_objects.status` → `pushed` (or `push_failed`), `m3ter_id` stored

**State Management:**
- Backend: LangGraph `AsyncPostgresSaver` checkpoints `WorkflowState` TypedDict per `thread_id` in Postgres (allows resume after disconnect)
- Backend: LangGraph `AsyncPostgresStore` persists long-term memory in 4 namespaces; accessed via `config["configurable"]["__pregel_runtime"].store`
- Frontend: Class-based Svelte 5 runes stores (`$state`, `$derived`) — no Svelte 4 legacy writable stores

## Key Abstractions

**WorkflowState TypedDict:**
- Purpose: Single flat TypedDict shared across all 4 workflow graphs; all entity batches, errors, decisions, and memory fields live here
- Location: `backend/app/agents/state.py`
- Pattern: Each workflow uses only its relevant slices; total=False so all keys are optional

**LangGraph StateGraph (Compiled):**
- Purpose: Declarative DAG of async node functions with conditional edges; compiled once and cached as module-level singleton
- Examples: `backend/app/agents/graphs/product_meter_agg.py`, `backend/app/agents/graphs/plan_pricing.py`, `backend/app/agents/graphs/account_setup.py`, `backend/app/agents/graphs/usage_submission.py`
- Pattern: `_build_graph()` constructs, `build_*_graph()` async function lazy-compiles with checkpointer+store, module-level `_compiled_graph` caches result

**Approval Node Pattern:**
- Purpose: Reusable node that reads `current_step` to dispatch to the correct entity batch, interrupts for user review, then on resume persists to DB and processes decisions
- Location: `backend/app/agents/nodes/approval.py`
- Pattern: `_STEP_CONFIG` dict maps `current_step` string → (EntityType, entities_key, errors_key, decisions_key, approved_step); single `approve_entities()` function handles all 10 entity types

**Validation Node Pattern:**
- Purpose: Reusable node that reads `current_step` to dispatch to the correct entity type's rule module
- Location: `backend/app/agents/nodes/validation.py`
- Pattern: `_STEP_TO_ENTITY` dict maps `current_step` → (EntityType, entities_key, errors_key, validated_step); calls `validate_entity()` from `validation/engine.py`

**M3terClient:**
- Purpose: Authenticated HTTP client to the m3ter Config API and Ingest API with token caching and retry
- Location: `backend/app/m3ter/client.py`
- Pattern: Class-level `_token_cache` (dict keyed by org_id), lazy-init `httpx.AsyncClient`, 3-attempt retry with backoff [1, 2, 5]s on 429/500/50x

**WorkflowStore (Frontend):**
- Purpose: Single unified Svelte 5 class store owning the WebSocketClient and all workflow/chat state
- Location: `frontend/src/lib/stores/workflow.svelte.ts`
- Pattern: Class instantiated once, exported as singleton; `$state` fields mutated by `handleMessage()` which dispatches on `WsServerMessage.type`

## Entry Points

**Backend Application:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app` (dev: `--reload`)
- Responsibilities: Creates FastAPI app, registers CORS, registers `AuthError` handler, registers `api_router`, manages lifespan (DB pool open/close, checkpointer pool close)

**Backend API Router:**
- Location: `backend/app/api/router.py`
- Triggers: Included by `main.py`
- Responsibilities: Aggregates 10 sub-routers into single `api_router`

**Frontend Application:**
- Location: `frontend/src/routes/+layout.svelte`
- Triggers: SvelteKit SSR/CSR bootstrap
- Responsibilities: Root layout, Supabase auth state subscription, `ModeWatcher`, `Toaster`

**Frontend Server Hooks:**
- Location: `frontend/src/hooks.server.ts`
- Triggers: Every server-side request
- Responsibilities: Creates Supabase SSR server client, attaches `safeGetSession()` to `event.locals`

**WebSocket Endpoints:**
- Location: `backend/app/api/ws.py`
- Endpoints: `/ws/workflows/{id}` (HITL workflow), `/ws/push/{use_case_id}` (push progress), `/ws/documents/{project_id}` (document processing observer), `/ws/generate/{project_id}` (use case generator)

## Error Handling

**Strategy:** Fail-fast with structured error propagation; memory operations are always wrapped in try/except (additive, never required)

**Patterns:**
- HTTP errors: `HTTPException` raised in service layer, propagated to FastAPI default handler
- Auth errors: `AuthError` custom exception handled by `main.py` handler, returns `{status_code, detail}`
- Graph errors: `current_step == "error"` set in state; `workflow_service.py` and `ws.py` both check `aget_state()` after `ainvoke()` for this condition, update DB status to `failed`
- WebSocket errors: Try/except around entire WS handler; `{type: "error", message}` sent to client before close
- LangGraph interrupt compatibility: `except GraphInterrupt: pass` kept for LangGraph 0.x; authoritative check is always `aget_state()` (LangGraph 1.x returns normally on interrupt)
- Memory errors: All `AsyncPostgresStore` operations wrapped in `try/except` — failures logged as warnings, workflow continues

## Cross-Cutting Concerns

**Logging:** Python `logging` module throughout backend; `logger = logging.getLogger(__name__)` per module; no structured logging library

**Validation:** Per-entity Pydantic v2 schemas for API request bodies; domain validation via `validation/engine.py` + `rules/` for generated entity data

**Authentication:**
- Backend REST: Supabase JWT via `Authorization: Bearer` header; `get_current_user` FastAPI dependency
- Backend WebSocket: JWT via `?token=` query parameter; `_authenticate_ws()` helper in `ws.py`
- Frontend: Supabase SSR client in `hooks.server.ts`; server-side `safeGetSession()` (calls `getUser()` first); route guard in `(app)/+layout.server.ts` redirects to `/login`

**LangSmith Tracing:** Enabled entirely via env vars (`LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`); `config` dict passed to `graph.ainvoke()` includes `run_name`, `metadata`, `tags`; no code changes required to toggle

---

*Architecture analysis: 2026-03-22*
