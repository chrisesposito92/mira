@AGENTS.md

<!-- GSD:project-start source:PROJECT.md -->
## Project

**m3ter Integration Architecture Diagrammer**

A configurator-style diagram builder inside MIRA that lets m3ter Solutions Engineers assemble branded integration architecture diagrams showing how m3ter connects to a prospect's existing tech stack. SEs configure systems and connections through a builder UI, see a live preview in m3ter's visual style, and export polished PNG/SVG images for presentations and proposals.

**Core Value:** An SE can produce a professional, customer-ready integration architecture diagram in minutes instead of hand-drawing on calls or cobbling together slides.

### Constraints

- **Tech stack**: Must use existing MIRA stack (SvelteKit, Tailwind v4, shadcn-svelte, Supabase, FastAPI)
- **Visual fidelity**: Exported diagrams must look comparable to m3ter's existing branded architecture diagrams
- **Logo sourcing**: Need a reliable approach for company/tool logos (bundled SVGs, CDN, or API)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.12+ (requires-python = ">=3.12") — backend FastAPI app, LangGraph agents, RAG pipeline, scripts
- TypeScript 5.9 — entire SvelteKit frontend, strict mode enabled
- SQL — Postgres migrations in `backend/migrations/*.sql`
- JSON — shared constants in `shared/constants.json`
## Runtime
- Node.js 24.13.0 (current system) — frontend dev server and build tooling
- Python 3.12+ (venv at `backend/.venv`) — backend API and agent workflows
- npm (frontend) — lockfile: `frontend/package-lock.json`, `package-lock.json` (root)
- pip/hatchling (backend) — lockfile: `backend/pyproject.toml` (no separate lockfile)
## Frameworks
- FastAPI 0.115+ — HTTP API server; entry point `backend/app/main.py`, mounted at port 8000
- Uvicorn (standard extras) — ASGI server with `--reload` for development
- Pydantic v2 10.0+ — all schemas/settings via `BaseSettings` and Pydantic models
- pydantic-settings 2.7+ — settings loaded from `backend/.env` via `backend/app/config.py`
- SvelteKit 2.50+ — full-stack framework; `frontend/src/routes/` for routing
- Svelte 5.51+ — component model (uses runes: `$state`, `$derived`, `$effect`; no legacy stores)
- Vite 7.3 — frontend build tool configured in `frontend/vite.config.ts`
- LangGraph 0.2+ — StateGraph-based agent workflows; graphs in `backend/app/agents/graphs/`
- LangChain 0.3+ — base abstractions; `init_chat_model()` for multi-provider LLM routing
- langgraph-checkpoint-postgres 2.0+ — `AsyncPostgresSaver` for workflow state persistence
- asyncpg 0.30+ — raw async PostgreSQL driver for checkpointer pool and RAG queries
- Tailwind CSS v4.2 — configured via `@theme` CSS blocks (no `tailwind.config.js`); Vite plugin via `@tailwindcss/vite`
- shadcn-svelte 1.1 — component library; config at `frontend/components.json` (baseColor: zinc)
- bits-ui 2.16 — headless primitives underlying shadcn-svelte
- mode-watcher 1.1 — dark mode toggle (no manual class toggling)
- lucide-svelte 0.575 — icon set
- pytest 8.0+ — test runner; config in `backend/pyproject.toml` (`asyncio_mode = "auto"`)
- pytest-asyncio 0.24+ — async test support
- scipy 1.14+ (dev) — Hungarian algorithm for eval accuracy scoring
- Vitest 4.0 — test runner; config at `frontend/vitest.config.ts` (jsdom environment)
- Testing Library: `@testing-library/svelte`, `@testing-library/user-event`, `@testing-library/jest-dom`
- `@sveltejs/adapter-vercel` 6.3 — Vercel deployment adapter (not adapter-auto); set in `frontend/svelte.config.js`
- `@sveltejs/vite-plugin-svelte` 6.2 — Svelte Vite integration
- husky 9.1 + lint-staged 16.3 — pre-commit hooks; root `package.json`
## Key Dependencies
- `supabase>=2.11.0` — Supabase Python client for auth and DB operations; `backend/app/db/client.py`
- `PyJWT[crypto]>=2.8.0` — JWT verification for Supabase tokens (HS256 + ES256); `backend/app/auth/jwt.py`
- `cryptography>=44.0.0` — Fernet encryption for m3ter API credentials at rest; `backend/app/m3ter/encryption.py`
- `httpx>=0.28.0` — async HTTP client for m3ter API calls; `backend/app/m3ter/client.py`
- `m3ter>=0.8.0` — official m3ter Python SDK (used alongside custom client)
- `langchain-openai>=0.3.0` — OpenAI LLM provider for LangChain
- `langchain-anthropic>=0.3.0` — Anthropic LLM provider for LangChain
- `langchain-google-genai>=2.0.0` — Google GenAI LLM provider for LangChain
- `langchain-tavily>=0.1.0` — Tavily web search tool for use case research node
- `langsmith>=0.3.0` — LangSmith tracing (optional, env-var activated)
- `openai>=1.60.0` — direct OpenAI client for embeddings (`text-embedding-3-small`); `backend/app/rag/embeddings.py`
- `langchain-text-splitters>=0.3.0` — document chunking for RAG ingestion
- `playwright>=1.49.0` — browser automation for doc scraping
- `beautifulsoup4>=4.12.0` — HTML parsing in scraper
- `python-docx>=1.1.0` — DOCX document text extraction
- `pypdf>=5.0.0` — PDF document text extraction
- `websockets>=14.0` — WebSocket support
- `python-multipart>=0.0.18` — multipart file upload parsing
- `@supabase/ssr>=0.8.0` — Supabase SSR client; used in `frontend/src/hooks.server.ts` and layouts
- `@supabase/supabase-js>=2.98.0` — Supabase browser client
- `codemirror>=6.0.2` + `@codemirror/lang-json` + `@codemirror/lint` — JSON editor in `frontend/src/lib/components/control-panel/JsonEditor.svelte`
- `tailwind-merge>=3.5.0` + `clsx>=2.1.1` — `cn()` utility in `frontend/src/lib/utils.ts`
- `svelte-sonner>=1.0.7` — toast notifications
## Configuration
- Loaded from `backend/.env` via pydantic-settings `BaseSettings` in `backend/app/config.py`
- Required: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `ENCRYPTION_KEY`, `TAVILY_API_KEY`
- Optional: `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` (defaults to `"mira"`)
- LangSmith vars are explicitly exported to `os.environ` by `backend/app/config.py` at import time
- SvelteKit `$env/static/public` module — prefix `PUBLIC_` for client-exposed vars
- Required: `PUBLIC_SUPABASE_URL`, `PUBLIC_SUPABASE_ANON_KEY`, `PUBLIC_API_URL`, `PUBLIC_WS_URL`
- Backend: `backend/pyproject.toml` (hatchling build system)
- Frontend: `frontend/vite.config.ts`, `frontend/svelte.config.js`, `frontend/tsconfig.json`
- Root scripts: `package.json` delegates to `frontend/` and `backend/` subpackages
- Pre-commit: `package.json` husky hooks run prettier on frontend files and ruff on backend `.py` files
- Backend: Ruff 0.8+ (`select = ["E", "F", "I", "N", "W", "UP"]`, line-length 100); config in `backend/pyproject.toml`
- Frontend: ESLint 10 (`frontend/eslint.config.js`) + Prettier 3.8 (`frontend/.prettierrc`)
## Platform Requirements
- Docker (for local Supabase stack via `docker-compose.yml`)
- Python 3.12 or 3.13 (not 3.14) with venv at `backend/.venv`
- Node.js 24+ for frontend tooling
- Frontend: Vercel (adapter-vercel in `frontend/svelte.config.js`)
- Backend: Any ASGI-compatible host (uvicorn); Supabase for DB and auth
- Database: PostgreSQL 15.8 with `pgvector` and `pgcrypto` extensions (see `backend/migrations/001_extensions.sql`)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Python (backend)
### Naming Patterns
- Module names use `snake_case` throughout: `project_service.py`, `llm_factory.py`, `cross_entity.py`
- Test files are prefixed `test_`: `test_api_generated_objects.py`, `test_plan_pricing_graph.py`
- Node modules are short verbs or compound nouns: `generation.py`, `validation.py`, `load_approved.py`
- All public functions use `snake_case`: `validate_entity()`, `create_project()`, `get_current_user()`
- Private helpers use leading underscore: `_format_clarification_answers()`, `_make_llm_response()`, `_build_graph()`
- Async functions always marked `async def`; no sync wrappers around async logic
- `snake_case` throughout: `use_case_id`, `model_id`, `plan_template_errors`
- Module-level constants use `SCREAMING_SNAKE_CASE`: `CODE_PATTERN`, `VALID_CATEGORIES`, `MOCK_USER_ID`
- Module-level registries also use uppercase: `MODEL_REGISTRY`, `PUSH_ORDER`
- `PascalCase`: `ProjectCreate`, `MockPostgrestBuilder`, `M3terClient`, `ValidationError`
- Pydantic schemas always follow `{Entity}{Create|Update|Response}` pattern
- TypedDicts use `PascalCase` and declare `total=False` when all fields optional: `WorkflowState`
- Enum fields defined in `app/schemas/common.py` as `EntityType`, accessed as `EntityType.product`
### Code Style
- Ruff handles both linting and formatting (configured in `backend/pyproject.toml`)
- Line length: **100 characters**
- Target Python version: **3.12**
- Active rule sets: `E` (pycodestyle errors), `F` (pyflakes), `I` (isort), `N` (naming), `W` (warnings), `UP` (pyupgrade)
- `from datetime import UTC` — never `timezone.utc` (UP017)
- `str | None` union syntax, not `Optional[str]` (UP006/UP007)
- `list[dict]` lowercase generics, not `List[Dict]` (UP006)
### Import Organization
- Local imports use absolute paths from `app.*` root — no relative imports
- `from app.dependencies import get_current_user, get_supabase` is the canonical DI import
### Module Design
- One file per resource: `projects.py`, `use_cases.py`, `generated_objects.py`
- Always define `router = APIRouter(prefix="/api/...", tags=[...])`
- Route handlers are thin: extract params, call service, return result
- All route handlers are `async def` with type annotations including return type
- Service functions are plain synchronous functions (Supabase SDK is sync)
- Signature convention: `func(supabase: Client, user_id: UUID, ...) -> dict | list[dict]`
- Ownership checks before any mutation — raise `HTTPException(404)` if not found
- Use `data.model_dump(exclude_unset=True)` for partial updates
- Per-entity modules in `validation/rules/` each expose a single `validate(data: dict) -> list[ValidationError]` function
- Shared field validators in `validation/common.py`: `validate_name()`, `validate_code()`, `validate_non_negative()`
- `ValidationError` is a `@dataclass` with `field`, `message`, `severity` ("error" | "warning")
- Dispatch goes through `validate_entity(entity_type, data)` in `validation/engine.py`
- Each node is an `async def` function: `async def generate_products(state: WorkflowState, config: RunnableConfig) -> dict`
- Nodes return partial state dicts — only the keys they update
- LLM calls follow: `llm = get_llm(model_id); response = await llm.ainvoke([SystemMessage(...), HumanMessage(...)])`
- Parse LLM output with `parse_entity_list(content)` and `extract_llm_text()`
- Memory operations are always wrapped in `try/except` — memory is additive, never required
### Error Handling
- Service layer raises `HTTPException` directly: `raise HTTPException(status_code=404, detail="Project not found")`
- Custom `AuthError` exception in `app/auth/jwt.py` — handled globally in `app/main.py` via `@app.exception_handler(AuthError)`
- LangGraph node errors set `state["error"]` and `state["current_step"] = "error"` — never raise
- `pytest.skip()` used in integration tests when infrastructure is unavailable (not `pytest.fail()`)
### Logging
- Every agent node module declares `logger = logging.getLogger(__name__)` at module level
- No log calls in service layer — logging is at the agent/node level
### Comments / Docstrings
## TypeScript / Svelte (frontend)
### Naming Patterns
- SvelteKit routes use `+page.svelte`, `+layout.svelte`, `+page.server.ts` conventions
- Component files: `PascalCase.svelte` — `ProjectCard.svelte`, `ObjectEditor.svelte`
- Store files: `kebab-case.svelte.ts` — `objects.svelte.ts`, `workflow.svelte.ts`
- Service files: `kebab-case.ts` — `api.ts`, `generated-objects.ts`, `push-websocket.ts`
- Type files: `kebab-case.ts` — `workflow.ts`, `push.ts`, `document.ts`
- Test files: co-located, same name + `.test.ts` — `objects.svelte.test.ts`, `ProjectCard.svelte.test.ts`
- `camelCase` for all variables and functions: `createWorkflowService()`, `mockObjectService()`, `makeMockObject()`
- `PascalCase` for classes: `ObjectsStore`, `ApiClient`, `ApiError`
- Exported constants use `SCREAMING_SNAKE_CASE`: `ENTITY_TYPE_ORDER`, `OBJECT_STATUSES`, `PUSHABLE_STATUSES`
- Interfaces use `PascalCase`: `WorkflowService`, `EntityGroup`, `GeneratedObjectService`
- Discriminated union type aliases for domain enums: `EntityType`, `ObjectStatus`, `WorkflowType`
- All domain types are defined and re-exported from `src/lib/types/index.ts`
### Code Style
- Prettier with `prettier-plugin-svelte` and `prettier-plugin-tailwindcss`
- Tab-based indentation (Prettier default for Svelte)
- Double quotes for strings (Prettier default)
- ESLint with `typescript-eslint` + `eslint-plugin-svelte`
- `@typescript-eslint/no-explicit-any` is disabled in test files only
- `svelte/no-navigation-without-resolve`, `svelte/require-each-key`, `no-useless-assignment` are disabled for shadcn-svelte component compatibility
- All reactive state uses `$state`: `objects = $state<GeneratedObject[]>([])`
- Derived values use `$derived` or `$derived.by()` for complex derivations
- Never use legacy `writable()` or `readable()` stores
- All `<script>` blocks must have `lang="ts"`
### Import Organization
- `$lib` → `src/lib`
- `$components` → `src/lib/components`
- `$stores` → `src/lib/stores`
- `$services` → `src/lib/services`
- `$types` → `src/lib/types`
- External packages first, then `$lib/*` aliases
- Types imported with `import type { ... }` when type-only
### Module Design
- `cn(...classes)` from `$lib/utils.ts` for all conditional Tailwind class merging — never raw string concatenation
### Error Handling
- Service methods throw `ApiError` (custom class in `src/lib/services/api.ts`) for non-OK HTTP responses
- Stores catch errors and set `store.error = e.message` — never propagate to components
- Store methods return result objects: `{ ok: true, created: obj }` or `{ ok: false, error: string }` for operations with meaningful failures
### Comments
- Complex `$derived.by()` logic
- Non-obvious WebSocket protocol notes
- Disambiguating shadcn-svelte workarounds
## Shared (`shared/` directory)
- JSON files only — entity type lists, status enums, shared constants
- Consumed by both frontend (via import) and backend (via Python file reads)
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Monorepo: FastAPI backend (Python) + SvelteKit frontend (TypeScript) + JSON shared constants
- Four sequential LangGraph `StateGraph` workflows (WF1→WF2→WF3→WF4), each producing m3ter billing entity types; each workflow gates on its predecessor completing
- Real-time bidirectional WebSocket layer (`ws.py`) drives the HITL interrupt/resume cycle alongside optional REST polling
- Long-term memory via `AsyncPostgresStore` (4 namespaces) enriches generation context across workflow runs; short-term state checkpointed via `AsyncPostgresSaver`
- Supabase (PostgreSQL + Auth + Storage) is the single source of truth for all persistent data; the backend uses service-role key (bypasses RLS) with ownership checks in service layer
## Layers
- Purpose: Receive HTTP/WebSocket requests, enforce auth, delegate to service layer
- Location: `backend/app/api/`
- Contains: `router.py` (aggregates all sub-routers), 10 route modules (`projects.py`, `use_cases.py`, `workflows.py`, `ws.py`, `generated_objects.py`, `documents.py`, `org_connections.py`, `chat_messages.py`, `m3ter_sync.py`, `use_case_generator.py`)
- Depends on: `app.dependencies` (auth DI), `app.services.*`, `app.schemas.*`
- Used by: External clients (SvelteKit frontend, API consumers)
- Purpose: Provide auth-verified user_id and Supabase client to route handlers
- Location: `backend/app/dependencies.py`
- Contains: `get_current_user()` (Bearer JWT → UUID), `get_supabase()` (Supabase service-role client)
- Depends on: `app.auth.jwt.verify_token`, `app.db.client`
- Used by: All API route handlers via `Depends()`
- Purpose: Business logic, ownership verification, orchestration; decoupled from HTTP concerns
- Location: `backend/app/services/`
- Contains: `workflow_service.py` (graph start/resume/get), `push_service.py` (m3ter entity push orchestration), `generated_object_service.py`, `project_service.py`, `use_case_service.py`, `document_service.py`, `document_processor.py`, `chat_message_service.py`, `org_connection_service.py`, `document_processing_registry.py`
- Depends on: `app.db.client`, `app.m3ter.*`, `app.rag.*`, `app.agents.graphs.*`
- Used by: API layer
- Purpose: LangGraph StateGraph definitions, nodes, prompts, memory, LLM factory
- Location: `backend/app/agents/`
- Contains: `graphs/` (4 workflow graphs + use case generator graph), `nodes/` (14 node modules), `prompts/` (3 prompt modules), `tools/` (RAG tool, m3ter schema), `state.py` (WorkflowState + UseCaseGenState TypedDicts), `llm_factory.py` (6-model registry), `checkpointer.py` (AsyncPostgresSaver + AsyncPostgresStore), `memory.py`, `memory_decisions.py`, `memory_rag.py`, `utils.py`
- Depends on: `app.db.client`, `app.rag.*`, `app.validation.*`, `app.schemas.*`, LangChain/LangGraph
- Used by: `workflow_service.py`, `ws.py`
- Purpose: Per-entity rule enforcement before user approval; also used by object creation endpoint
- Location: `backend/app/validation/`
- Contains: `engine.py` (`validate_entity()` dispatcher), `common.py` (shared helpers), `cross_entity.py` (referential integrity), `rules/` (10 per-entity modules: `product.py`, `meter.py`, `aggregation.py`, `compound_aggregation.py`, `plan_template.py`, `plan.py`, `pricing.py`, `account.py`, `account_plan.py`, `measurement.py`)
- Depends on: `app.schemas.common`
- Used by: `nodes/validation.py`, `api/generated_objects.py`
- Purpose: OAuth2 client, reference resolution, payload mapping, ordered entity push
- Location: `backend/app/m3ter/`
- Contains: `client.py` (M3terClient — HTTP Basic auth token endpoint, class-level token cache 4h50m, retry logic 429/500/50x), `mapper.py` (allowlist-based MIRA→m3ter payload transformation), `entities.py` (PUSH_ORDER list, ReferenceResolver, `push_entities_ordered()`), `encryption.py` (Fernet credential encryption)
- Depends on: `app.schemas.common`, `app.agents.tools.m3ter_schema`
- Used by: `push_service.py`
- Purpose: Text chunking, OpenAI embeddings, pgvector ingestion, two-source retrieval
- Location: `backend/app/rag/`
- Contains: `chunker.py`, `embeddings.py` (batch OpenAI embedding via `text-embedding-3-small`), `ingestion.py`, `retriever.py` (two-source cosine similarity: `m3ter_docs` + project-scoped `user_document`)
- Depends on: `app.db.client` (asyncpg pool), `app.config`
- Used by: `agents/tools/rag_tool.py`, `services/document_service.py`
- Purpose: Connection pool management and Supabase client singletons
- Location: `backend/app/db/`
- Contains: `client.py` (module-level singletons: `_supabase_client` service-role, `_supabase_anon_client`, `_db_pool` asyncpg)
- Depends on: `app.config`
- Used by: All layers that need DB access
- Purpose: JWT verification (Supabase-issued tokens)
- Location: `backend/app/auth/`
- Contains: `jwt.py` (Supabase JWT verification, `AuthError` exception), middleware wired in `main.py`
- Depends on: `app.config` (JWT secret)
- Used by: `app.dependencies`, `ws.py` (WebSocket token auth via query param)
- Purpose: Pydantic v2 request/response models and shared StrEnums
- Location: `backend/app/schemas/`
- Contains: `common.py` (`EntityType`, `ObjectStatus`, `WorkflowType`, `WorkflowStatus`, `UseCaseStatus`, `MessageRole`, `BillingFrequency`, `ConnectionStatus`, `DocumentStatus`), plus per-domain schema files
- Depends on: pydantic
- Used by: All layers
- Purpose: Svelte 5 runes-based client state management (class-based singletons)
- Location: `frontend/src/lib/stores/`
- Contains: `workflow.svelte.ts` (WorkflowStore — WS connection, messages, pending HITL interactions), `objects.svelte.ts` (ObjectsStore — generated object list, filtering, push session), `project.svelte.ts`, `auth.svelte.ts`, `org-connections.svelte.ts`
- Depends on: `$lib/services/*`, `$lib/types`
- Used by: SvelteKit route components
- Purpose: HTTP/WebSocket API client wrappers (factory functions)
- Location: `frontend/src/lib/services/`
- Contains: `api.ts` (base ApiClient), `workflow.ts` (`createWorkflowService()`), `generated-objects.ts` (`createGeneratedObjectService()`), `websocket.ts` (WebSocketClient with exponential backoff), `push-websocket.ts`, `doc-websocket.ts`, `generator-websocket.ts`, `projects.ts`, `use-cases.ts`, `documents.ts`, `org-connections.ts`
- Depends on: Supabase auth for JWT token injection
- Used by: Stores, route page components
## Data Flow
- Backend: LangGraph `AsyncPostgresSaver` checkpoints `WorkflowState` TypedDict per `thread_id` in Postgres (allows resume after disconnect)
- Backend: LangGraph `AsyncPostgresStore` persists long-term memory in 4 namespaces; accessed via `config["configurable"]["__pregel_runtime"].store`
- Frontend: Class-based Svelte 5 runes stores (`$state`, `$derived`) — no Svelte 4 legacy writable stores
## Key Abstractions
- Purpose: Single flat TypedDict shared across all 4 workflow graphs; all entity batches, errors, decisions, and memory fields live here
- Location: `backend/app/agents/state.py`
- Pattern: Each workflow uses only its relevant slices; total=False so all keys are optional
- Purpose: Declarative DAG of async node functions with conditional edges; compiled once and cached as module-level singleton
- Examples: `backend/app/agents/graphs/product_meter_agg.py`, `backend/app/agents/graphs/plan_pricing.py`, `backend/app/agents/graphs/account_setup.py`, `backend/app/agents/graphs/usage_submission.py`
- Pattern: `_build_graph()` constructs, `build_*_graph()` async function lazy-compiles with checkpointer+store, module-level `_compiled_graph` caches result
- Purpose: Reusable node that reads `current_step` to dispatch to the correct entity batch, interrupts for user review, then on resume persists to DB and processes decisions
- Location: `backend/app/agents/nodes/approval.py`
- Pattern: `_STEP_CONFIG` dict maps `current_step` string → (EntityType, entities_key, errors_key, decisions_key, approved_step); single `approve_entities()` function handles all 10 entity types
- Purpose: Reusable node that reads `current_step` to dispatch to the correct entity type's rule module
- Location: `backend/app/agents/nodes/validation.py`
- Pattern: `_STEP_TO_ENTITY` dict maps `current_step` → (EntityType, entities_key, errors_key, validated_step); calls `validate_entity()` from `validation/engine.py`
- Purpose: Authenticated HTTP client to the m3ter Config API and Ingest API with token caching and retry
- Location: `backend/app/m3ter/client.py`
- Pattern: Class-level `_token_cache` (dict keyed by org_id), lazy-init `httpx.AsyncClient`, 3-attempt retry with backoff [1, 2, 5]s on 429/500/50x
- Purpose: Single unified Svelte 5 class store owning the WebSocketClient and all workflow/chat state
- Location: `frontend/src/lib/stores/workflow.svelte.ts`
- Pattern: Class instantiated once, exported as singleton; `$state` fields mutated by `handleMessage()` which dispatches on `WsServerMessage.type`
## Entry Points
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app` (dev: `--reload`)
- Responsibilities: Creates FastAPI app, registers CORS, registers `AuthError` handler, registers `api_router`, manages lifespan (DB pool open/close, checkpointer pool close)
- Location: `backend/app/api/router.py`
- Triggers: Included by `main.py`
- Responsibilities: Aggregates 10 sub-routers into single `api_router`
- Location: `frontend/src/routes/+layout.svelte`
- Triggers: SvelteKit SSR/CSR bootstrap
- Responsibilities: Root layout, Supabase auth state subscription, `ModeWatcher`, `Toaster`
- Location: `frontend/src/hooks.server.ts`
- Triggers: Every server-side request
- Responsibilities: Creates Supabase SSR server client, attaches `safeGetSession()` to `event.locals`
- Location: `backend/app/api/ws.py`
- Endpoints: `/ws/workflows/{id}` (HITL workflow), `/ws/push/{use_case_id}` (push progress), `/ws/documents/{project_id}` (document processing observer), `/ws/generate/{project_id}` (use case generator)
## Error Handling
- HTTP errors: `HTTPException` raised in service layer, propagated to FastAPI default handler
- Auth errors: `AuthError` custom exception handled by `main.py` handler, returns `{status_code, detail}`
- Graph errors: `current_step == "error"` set in state; `workflow_service.py` and `ws.py` both check `aget_state()` after `ainvoke()` for this condition, update DB status to `failed`
- WebSocket errors: Try/except around entire WS handler; `{type: "error", message}` sent to client before close
- LangGraph interrupt compatibility: `except GraphInterrupt: pass` kept for LangGraph 0.x; authoritative check is always `aget_state()` (LangGraph 1.x returns normally on interrupt)
- Memory errors: All `AsyncPostgresStore` operations wrapped in `try/except` — failures logged as warnings, workflow continues
## Cross-Cutting Concerns
- Backend REST: Supabase JWT via `Authorization: Bearer` header; `get_current_user` FastAPI dependency
- Backend WebSocket: JWT via `?token=` query parameter; `_authenticate_ws()` helper in `ws.py`
- Frontend: Supabase SSR client in `hooks.server.ts`; server-side `safeGetSession()` (calls `getUser()` first); route guard in `(app)/+layout.server.ts` redirects to `/login`
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
