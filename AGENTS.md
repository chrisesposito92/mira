Use your superpowers skills when applicable.

USE LANGSMITH MCP WHILE DEBUGGING WORKFLOWS. IT WILL ALLOW YOU TO SEE TRACES FOR FULL WORKFLOWS AT EACH INDIVIDUAL NODE, ETC. SUPER HELPFUL.

# MIRA — Metering Intelligence & Rating Architect

AI-powered m3ter configuration assistant. Generates correct m3ter billing configs through LangGraph agent workflows with human-in-the-loop approval gates.

## Commands

```bash
# Root-level (from /mira)
npm run dev:frontend          # SvelteKit dev server on :5173
npm run dev:backend           # FastAPI on :8000 (uvicorn --reload)
npm run build                 # Build frontend (Vercel adapter)
npm run check                 # svelte-check TypeScript validation
npm run test:frontend         # Vitest (colocated tests in src/**/*.test.ts)
npm run test:backend          # pytest (run from backend/ with venv active)
npm run lint:frontend         # eslint + prettier --check
npm run lint:backend          # ruff check
npm run format:backend        # ruff format

# Frontend (from frontend/)
npm run test                  # vitest run
npm run test:watch            # vitest (watch mode)
npm run lint                  # eslint . && prettier --check .
npm run lint:fix              # eslint . --fix && prettier --write .
npm run format                # prettier --write .

# Backend (must activate venv first)
cd backend && source .venv/bin/activate
pytest tests/ -v              # Run all backend tests (including integration)
pytest -m "not integration"   # Run unit tests only (no Supabase needed)
pytest tests/test_health.py   # Single test file

# Scraper & Embeddings (must activate venv first)
cd backend && source .venv/bin/activate
python -m scripts.scrape_m3ter_docs   # Scrape m3ter docs → backend/data/m3ter_docs/*.json
python -m scripts.seed_embeddings     # Seed pgvector from scraped JSON (requires DB + OpenAI key)

# Evals (must activate venv first)
cd backend && source .venv/bin/activate
pytest evals/ -m eval_live --model-id claude-sonnet-4-6 -v  # Live eval — single model
pytest evals/ -m eval_live -k "cloud_storage" -v            # Single example
python -m evals.run_eval --all-models                        # Multi-model comparison
python -m evals.run_eval --save-golden                       # Save golden responses

# Docker
docker compose up -d          # Local Supabase (postgres:54322, auth:54321, studio:54323)
```

## Architecture

Monorepo with three top-level packages:

- `backend/` — Python 3.12+, FastAPI + LangGraph agent workflows
- `frontend/` — SvelteKit + TypeScript + Tailwind v4 + shadcn-svelte
- `shared/` — Shared constants (entity types, status enums) as JSON

Full architecture: `docs/ARCHITECTURE.md`

### Backend Structure (`backend/app/`)

| Directory | Purpose |
|-----------|---------|
| `api/` | FastAPI route handlers |
| `agents/` | LangGraph StateGraphs, nodes, prompts, tools (see Agent Structure below) |
| `auth/` | Supabase JWT verification |
| `db/` | Supabase client, repository pattern |
| `m3ter/` | m3ter SDK wrapper, entity push, auth, credential encryption |
| `schemas/` | Pydantic v2 request/response models, shared enums |
| `rag/` | Text chunking, OpenAI embeddings, pgvector ingestion, two-source retrieval |
| `scraper/` | m3ter docs crawler (httpx + llms.txt manifest) |
| `services/` | Business logic layer |
| `validation/` | Per-entity validators + cross-entity checks |

### Agent Structure (`backend/app/agents/`)

| Directory | Purpose |
|-----------|---------|
| `state.py` | `WorkflowState` TypedDict — full graph state definition (WF1-WF4 fields + memory fields: `workflow_history`, `project_memory`, `correction_patterns`, `user_preferences`) |
| `llm_factory.py` | Multi-model registry + `get_llm()` via `init_chat_model()` (5 models) |
| `utils.py` | Shared helpers: `extract_interrupt_payload()`, `build_use_case_description()`, `parse_entity_list()` |
| `checkpointer.py` | `AsyncPostgresSaver` + `AsyncPostgresStore` setup, shared pool via `_get_pool()` |
| `memory.py` | Core long-term memory module — store access, namespace helpers, read/write ops for project context, corrections, workflow history |
| `memory_decisions.py` | User decision memory — entity diff engine, preference storage/retrieval/formatting per-user per-entity-type |
| `memory_rag.py` | RAG feedback memory — records approval signals per chunk, EMA scoring, feedback-based re-ranking |
| `nodes/analysis.py` | Analyze use case (fetch from DB + RAG + LLM) |
| `nodes/clarification.py` | Generate clarification questions with `interrupt()` |
| `nodes/generation.py` | Generate Products, Meters, Aggregations (separate functions) |
| `nodes/load_approved.py` | Load approved WF1 entities from DB for WF2 |
| `nodes/plan_template_gen.py` | PlanTemplate generation via LLM |
| `nodes/plan_gen.py` | Plan generation via LLM |
| `nodes/pricing_gen.py` | Pricing generation via LLM (5 strategies: tiered, volume, stairstep, per-unit, counter) |
| `nodes/load_approved_accounts.py` | Load approved WF1+WF2 entities from DB for WF3 |
| `nodes/load_approved_usage.py` | Load approved WF1+WF3 entities (meters, accounts) for WF4 |
| `nodes/account_gen.py` | Account generation via LLM |
| `nodes/account_plan_gen.py` | AccountPlan generation via LLM |
| `nodes/measurement_gen.py` | Measurement generation via LLM |
| `nodes/validation.py` | Run validation rules on generated entities (4-tuple step mapping + cross-entity validation) |
| `nodes/approval.py` | Persist entities to DB, `interrupt()` for user approval (5-tuple step config) |
| `graphs/product_meter_agg.py` | WF1 StateGraph: analyze → [clarify?] → generate → validate → approve (×4 entity types: Product, Meter, Aggregation, CompoundAggregation) |
| `graphs/plan_pricing.py` | WF2 StateGraph: load_approved → generate → validate → approve (×3: PlanTemplate, Plan, Pricing) |
| `graphs/account_setup.py` | WF3 StateGraph: load_approved → generate → validate → approve (×2: Account, AccountPlan) |
| `graphs/usage_submission.py` | WF4 StateGraph: load_approved → generate → validate → approve (×1: Measurement) |
| `prompts/product_meter.py` | System prompts for WF1 (Products, Meters, Aggregations) |
| `prompts/plan_pricing.py` | System prompts for WF2 (PlanTemplates, Plans, Pricing with 5 pricing strategies) |
| `prompts/account_usage.py` | System prompts for WF3+WF4 (Accounts, AccountPlans, Measurements) |
| `nodes/use_case_research.py` | Use case generator: Tavily web search + LLM summary |
| `nodes/use_case_clarify.py` | Use case generator: clarification questions with `interrupt()` |
| `nodes/use_case_compile.py` | Use case generator: compile research into UseCaseCreate dicts |
| `graphs/use_case_gen.py` | Use case generator StateGraph: research → [clarify?] → compile → END |
| `prompts/use_case_gen.py` | System prompts for use case generator (research + compilation) |
| `tools/rag_tool.py` | RAG retrieval wrapper for agent nodes |
| `tools/m3ter_schema.py` | Hardcoded m3ter entity schemas (Product, Meter, Aggregation, CompoundAggregation, PlanTemplate, Plan, Pricing, Account, AccountPlan, Measurement) |

### Frontend Structure (`frontend/src/`)

| Directory | Purpose |
|-----------|---------|
| `lib/components/ui/` | shadcn-svelte base components |
| `lib/components/chat/` | Chat UI (ChatContainer, EntityCard, ClarificationCard, WorkflowLauncher, etc.) |
| `lib/components/control-panel/` | ObjectTree, ObjectTreeNode, ObjectEditor, JsonEditor (CodeMirror 6), BulkActions, PushProgressPanel, PushConfirmDialog |
| `lib/components/project/` | Project/use case cards, FileUpload (drag-drop + progress), UploadProgressBar |
| `lib/components/layout/` | Sidebar, header, breadcrumbs |
| `lib/stores/` | Svelte 5 runes ($state-based) |
| `lib/services/` | API client layer |
| `lib/types/` | TypeScript type definitions |
| `routes/(auth)/` | Login, register (centered layout) |
| `routes/(app)/` | Authenticated routes (sidebar layout) |

### Path Aliases (frontend)

- `$lib` → `src/lib`
- `$components` → `src/lib/components`
- `$stores` → `src/lib/stores`
- `$services` → `src/lib/services`
- `$types` → `src/lib/types`

## Code Style

### Python (backend)
- Ruff for linting + formatting, line length 100
- Pydantic v2 for all schemas/settings
- `async def` for all route handlers
- Type hints on all functions
- Ruff rules: E, F, I (isort), N (naming), W, UP (pyupgrade)

### TypeScript (frontend)
- Svelte 5 with runes (`$state`, `$derived`, `$effect`) — no legacy stores
- `lang="ts"` on all `<script>` blocks
- Use `cn()` from `$lib/utils` for conditional class merging
- Tailwind v4 with CSS `@theme` variables (not tailwind.config.js)
- shadcn-svelte components in `$lib/components/ui/`

## Key Patterns

- **HITL**: LangGraph `interrupt()` → WebSocket sends to frontend → user approves/edits/rejects → `Command(resume=decision)`
- **Entity push order**: Product → Meter → Aggregation → PlanTemplate → Plan → Pricing → Account → AccountPlan (Config API). Measurements are submitted separately via the Ingest API. (CompoundAggregation is excluded from push — no mapper or schema support.)
- **m3ter auth**: OAuth2 client credentials per org (HTTP Basic auth), tokens cached 4h50m (10min buffer on 5hr m3ter token)
- **RAG**: Two-source retrieval (m3ter docs + user docs), pgvector cosine similarity, feedback-based re-ranking when store available (2x candidates → blended score: 0.7 * cosine + 0.3 * feedback)
- **Long-term memory**: LangGraph `AsyncPostgresStore` with 4 namespaces: `("project", id, "analysis")` for project-level domain knowledge, `("project", id, "workflow_history")` for cross-workflow summaries, `("user", id, "preferences", entity_type)` for user editing patterns, `("project", id, "rag_feedback")` for RAG chunk quality signals. All memory ops are wrapped in try/except — additive, never required. Nodes access store via `config["configurable"]["__pregel_runtime"].store`.
- **Checkpointing**: LangGraph AsyncPostgresSaver, resume by thread_id
- **Workflow API**: `POST /api/use-cases/{id}/workflows/start` → `POST /api/workflows/{id}/resume` (REST) or `ws://host/ws/workflows/{id}` (WebSocket)
- **LLM models**: gpt-5.2, gpt-5.4, gemini-3-flash-preview, gemini-3.1-pro-preview, claude-opus-4-6, claude-sonnet-4-6 — `GET /api/models` lists all
- **Validation**: Per-entity rule modules (`validation/rules/`) → `ValidationError` dataclass with field, message, severity. Shared helpers in `validation/common.py` (`validate_name`, `validate_code`, `validate_code_format`, `validate_custom_fields`, `validate_non_negative`). Covers: product, meter, aggregation, compound_aggregation, plan_template, plan, pricing, account, account_plan, measurement. Cross-entity referential integrity checks in `validation/cross_entity.py` (AccountPlan→Account/Plan, Measurement→Meter/Account).
- **Multi-workflow**: `workflow_type` field selects graph via `get_graph()` helper (product_meter_aggregation, plan_pricing, account_setup, usage_submission). Prerequisite chain: WF1 → WF2 → WF3 → WF4. Frontend WorkflowLauncher gates each workflow on predecessor completion.
- **LangSmith tracing**: Set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` in `.env` to enable automatic tracing of all LangGraph/LangChain calls. Graph invocation configs include `run_name`, `metadata` (workflow_id, workflow_type, source), and `tags` for filtering in the LangSmith dashboard. No code changes needed to toggle — purely env-var driven.

### Frontend Chat Interface

- **WorkflowStore**: Single unified store (`stores/workflow.svelte.ts`) — manages messages, workflow state, WS connection, pending interactions. No separate WebSocket store.
- **WebSocketClient**: Class in `services/websocket.ts` — NOT a singleton, owned by WorkflowStore. Auto-reconnect with exponential backoff (1s→30s, max 5 attempts).
- **WorkflowService**: Factory function `createWorkflowService(client)` in `services/workflow.ts` — REST calls for start, get, list, models, messages.
- **Chat messages**: Persisted to `chat_messages` DB table via `save_message_internal()` at 7 WS flow points. `GET/POST /api/workflows/{id}/messages` endpoints with ownership checks.
- **Component tree**: Control panel page → `WorkflowDrawer` (Sheet) → `WorkflowHeader` + `ChatContainer` → `ChatMessage` (dispatcher) → `EntityCard` | `ClarificationCard` | status/complete/error renders.
- **Interactive vs historical**: Only the last `entities`/`clarification` message shows action buttons. Prior ones display as read-only summaries.
- **Entity decisions**: Accumulated per-entity in store; auto-submitted when all entities have decisions.
- **Workflow UI**: No standalone route — workflows launch in a Sheet (right-side drawer) from the control panel. `WorkflowDrawer` wraps `WorkflowHeader` + `ChatContainer`. `WorkflowLauncherDropdown` in the control panel toolbar provides workflow type + model selection.
- **Chat message types**: Discriminated union `ChatMessage` with 7 variants: `status`, `entities`, `clarification`, `user_decision`, `user_clarification`, `complete`, `error`.

### Frontend Control Panel

- **ObjectsStore**: Class-based Svelte 5 runes singleton (`stores/objects.svelte.ts`) — manages objects list, filtering (entity type, status, search), tree grouping by entity type in push order, multi-select, single-object selection, CRUD operations (including `createObject`).
- **GeneratedObjectService**: Factory function `createGeneratedObjectService(client)` in `services/generated-objects.ts` — REST calls for listObjects, getObject, updateObject, bulkUpdateStatus, createObject, getTemplates, pushObject, pushObjects, getPushStatus.
- **Control panel route**: `/projects/[projectId]/use-cases/[useCaseId]/control-panel/` — primary use case view. 2-panel layout with ObjectTree (left) + ObjectEditor (right), BulkActions toolbar above, "Run Workflow" button + "New Object" button. Workflow chat opens in a Sheet drawer from the right. Auto-refetches objects when workflow produces new entities.
- **CreateObjectDialog**: Modal dialog (`components/control-panel/CreateObjectDialog.svelte`) — entity type selector (9 types, excludes `compound_aggregation` which has no schema/validator), name/code fields, JsonEditor with per-entity-type templates. JSON shape validated before submission. Dialog stays open on failure to preserve user input. Returns `boolean` from `oncreate` callback to signal success/failure.
- **Object templates**: `GET /api/objects/templates` returns JSON templates per entity type, generated from `m3ter_schema.py` schemas with sensible defaults.
- **Manual object creation**: `POST /api/use-cases/{id}/objects` creates objects with server-side validation via `validate_entity()`. Objects start as `draft` with any validation errors serialized.
- **JsonEditor**: CodeMirror 6 integration (`components/control-panel/JsonEditor.svelte`) — JSON syntax highlighting, linting, dark mode via mode-watcher, line numbers, bracket matching, fold gutters.
- **Tree structure**: Objects grouped by entity type in push order (product → meter → aggregation → ... → measurement). Collapsible groups with count badges. Supports multi-select via checkboxes.
- **StatusBadge**: Extended with object statuses: approved (blue), rejected (muted), pushed (green), push_failed (red). The "pushing" state is rendered via a `Loader2` spinner in `ObjectTreeNode.svelte` (not via StatusBadge).

### m3ter Push & Sync

- **M3terClient**: Enhanced OAuth2 client (`m3ter/client.py`) — HTTP Basic auth for token endpoint, class-level token cache with 4h50m TTL, lazy-init persistent httpx client, retry logic (3 attempts, backoff [1, 2, 5]s, retryable: 429/500/502/503/504), per-entity create methods for all 9 entity types, Config API + Ingest API support.
- **Payload mapper**: Allowlist-based (`m3ter/mapper.py`) — per-entity-type field sets derived from `m3ter_schema.py`, strips internal fields (`id`, `index`), removes None values.
- **Reference resolver**: `ReferenceResolver` class (`m3ter/entities.py`) — maps MIRA UUIDs to m3ter UUIDs incrementally as entities push, pre-loads from already-pushed objects, raises `ReferenceResolutionError` on missing references.
- **Push engine**: `push_entities_ordered()` (`m3ter/entities.py`) — sorts by canonical PUSH_ORDER (product → meter → aggregation → plan_template → plan → pricing → account → account_plan), resolves references, maps payloads, pushes to m3ter, updates DB, stops chain on first failure. Supports async `on_progress` callback for real-time WebSocket streaming.
- **Push service**: `push_service.py` — orchestrates single/bulk push with ownership checks, status validation (approved/push_failed only), org connection resolution via project → org_connections chain, credential decryption.
- **Push API**: `GET /api/use-cases/{id}/push/status` (readiness info), `POST /api/objects/{id}/push` (single), `POST /api/use-cases/{id}/push` (bulk with optional object_ids filter).
- **Push WebSocket**: `ws://host/ws/push/{use_case_id}?token={token}` — real-time per-entity progress streaming. Client sends `start_push`, server streams `push_started` → `push_progress` (per entity) → `push_complete`.
- **Frontend push flow**: ObjectEditor "Push to m3ter" button (single push via REST) → BulkActions "Push Selected" button → PushConfirmDialog (AlertDialog with entity breakdown + dependency warning) → PushWebSocketClient (lightweight, no reconnect) → PushProgressPanel (progress bar, per-entity status icons, dismiss on complete).
- **ObjectsStore push state**: `pushSession` (active session tracking), `pushing` flag, `pushableSelectedIds` derived, `handlePushMessage()` updates both session and objects array from WS messages.

### Use Case Generator

- **Graph architecture**: Standalone LangGraph graph (`graphs/use_case_gen.py`) with `UseCaseGenState` TypedDict (separate from `WorkflowState`). Uses `MemorySaver` (not `AsyncPostgresSaver`) — sessions are ephemeral, no persistent checkpointing needed.
- **Tavily search**: `research_customer` node (`nodes/use_case_research.py`) calls Tavily web search API to find customer pricing/billing info, then summarizes via LLM. Requires `TAVILY_API_KEY` environment variable.
- **Graph flow**: `research_customer` → `should_clarify?` (conditional) → `ask_clarification` (interrupt/resume) → `compile_use_cases` → END. If no clarification needed, skips directly to compile.
- **Clarification node**: `nodes/use_case_clarify.py` — generates 1-3 questions with `interrupt()`, resumes with user answers.
- **Compilation node**: `nodes/use_case_compile.py` — generates `UseCaseCreate`-compatible dicts (title, description, billing_frequency, currency, target_billing_model).
- **Prompts**: `prompts/use_case_gen.py` — research and compilation system prompts.
- **WebSocket endpoint**: `ws://host/ws/generate/{project_id}?token={token}` — client sends `start_generate` (customer_name, num_use_cases, notes?, attachment_text?, model_id) and `clarify` (answers). Server sends `gen_status`, `gen_clarification`, `gen_use_cases`, `gen_error`.
- **REST endpoint**: `POST /api/projects/{project_id}/generate-use-cases/extract-text` — accepts file upload (PDF/DOCX/TXT/CSV), extracts text in-memory (no DB storage), returns plain text.
- **Frontend dialog**: `GenerateUseCasesDialog.svelte` (`components/project/`) — multi-step: input form (customer name, num use cases, model, notes, file upload) → progress indicators → clarification cards → use case result cards with selection and save.
- **Frontend types**: `types/generator.ts` — TypeScript types for generator WebSocket messages, state, and results.
- **Frontend WebSocket**: `services/generator-websocket.ts` — `GeneratorWebSocketClient` class for the generate endpoint.
- **Frontend result cards**: `components/project/UseCaseResultCard.svelte` — displays generated use case with select/deselect.

### Document Processing WebSocket

- **Async processing**: `upload_document()` returns immediately with "pending" status, fires `asyncio.create_task()` for background extraction/chunking/embedding.
- **Processing registry**: Module-level `document_processing_registry.py` bridges REST uploads to WebSocket observers. `_listeners` (project_id → [WebSocket]).
- **Document WebSocket**: `ws://host/ws/documents/{project_id}?token={token}` — passive observer, no client-to-server messages. Server streams `doc_processing_started` → `doc_processing_progress` (per stage) → `doc_processing_complete`.
- **Processing stages**: `extracting` → `chunking` → `embedding` (with chunk count detail) → `storing`. Progress callback (`on_progress`) in `process_document()` is forwarded to `ingest_document()` which calls it at each stage.
- **Frontend upload flow**: FileUpload drop zone → XHR upload with progress (`uploadWithProgress()`) → DocWebSocketClient (passive, lightweight) → UploadProgressBar (two-phase: upload % → stage indicators). ProjectStore manages `uploadProgress` state and WS message handling.
- **XHR for upload progress**: `DocumentService.uploadWithProgress()` uses XMLHttpRequest (not Fetch) for `upload.onprogress` events. `ApiClient.baseUrl` and `getAuthHeaders()` exposed as public.

### Frontend Auth (Supabase SSR)

- **Data flow**: `hooks.server.ts` → `+layout.server.ts` → `+layout.ts` → `+layout.svelte`
- **`hooks.server.ts`**: Creates `supabase` server client and `safeGetSession()` on `event.locals`. `safeGetSession` calls `getUser()` first (validates JWT server-side) then `getSession()` — never trust `getSession()` alone on the server.
- **`+layout.server.ts`**: Passes `session`, `user`, and only Supabase cookies (filtered by `sb-` prefix) to the universal layout. Never pass `cookies.getAll()` unfiltered — it leaks HttpOnly/sensitive cookies to the client.
- **`+layout.ts`**: Universal load creates `createBrowserClient` (client) or `createServerClient` (server) via `isBrowser()`. Calls `depends('supabase:auth')` so `invalidate('supabase:auth')` re-runs on auth changes.
- **`+layout.svelte`**: Subscribes to `onAuthStateChange` and calls `invalidate('supabase:auth')` when session changes. Includes `ModeWatcher` and `Toaster`.
- **Route guard**: `(app)/+layout.server.ts` checks session, redirects to `/login` if missing. All child routes of `(app)/` are protected.
- **Auth store**: Class-based Svelte 5 runes store (`$state`/`$derived`) — singleton `authStore` with `session`, `user`, `profile`, computed `displayName`/`userInitials`.
- **Redirect safety**: The `auth/confirm/+server.ts` endpoint validates the `next` param to prevent open redirects — only relative paths (starting with `/`, not `//`) are allowed.
- **Register flow**: `signUp()` branches on whether a session is returned — auto-confirm redirects to dashboard, email confirmation shows a "check your email" message.

## Environment Variables

### Backend (`backend/.env`)
`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `ENCRYPTION_KEY`, `TAVILY_API_KEY`, `LANGSMITH_TRACING` (optional), `LANGSMITH_API_KEY` (optional), `LANGSMITH_PROJECT` (optional, defaults to `mira`)

### Frontend (`frontend/.env`)
`PUBLIC_SUPABASE_URL`, `PUBLIC_SUPABASE_ANON_KEY`, `PUBLIC_API_URL`, `PUBLIC_WS_URL`

### Evaluation System (`backend/evals/`)

| Directory | Purpose |
|-----------|---------|
| `datasets/base.py` | Core dataclasses: EvalExample, ReferenceEntity, WorkflowReference, EvalResult |
| `datasets/cloud_storage.py` | Example 1: Cloud Storage reference config |
| `datasets/app_hosting.py` | Example 2: App Hosting with compound aggregation |
| `datasets/candidate_checks.py` | Example 3: Candidate Checks with segmented aggregation |
| `datasets/registry.py` | ALL_EXAMPLES list, get_example() helper |
| `evaluators/structural.py` | Structural validity (JSON, required fields, code format) |
| `evaluators/schema_compliance.py` | Reuses app.validation.engine.validate_entity() |
| `evaluators/completeness.py` | Entity count vs reference expected_counts |
| `evaluators/accuracy.py` | Fuzzy matching with Hungarian algorithm (scipy) |
| `evaluators/cross_entity.py` | Referential integrity checks |
| `evaluators/semantic.py` | LLM-as-Judge (claude-opus-4-6) for conceptual correctness |
| `evaluators/composite.py` | Weighted composite scorer + report formatting |
| `runner/auto_approver.py` | HITL interrupt loop: auto-approve all entities |
| `runner/graph_harness.py` | Graph compilation with MemorySaver, mock Supabase/RAG |
| `runner/workflow_chain.py` | WF1→WF2→WF3 chained execution |
| `test_eval_wf1.py` | WF1 pytest evals (parametrized by example) |
| `test_eval_wf2.py` | WF2 pytest evals |
| `test_eval_wf3.py` | WF3 pytest evals |
| `test_eval_chain.py` | Full WF1→WF2→WF3 chain eval |
| `run_eval.py` | Standalone CLI runner |

#### Reference Examples

3 examples based on [m3ter worked examples](https://docs.m3ter.com/guides/getting-started/metering-for-production-worked-examples):

| Example | WF1 Entities | WF2 Entities | Key Feature |
|---------|-------------|-------------|-------------|
| `cloud_storage` | 1 product, 1 meter (3 data fields + 1 derived), 3 aggregations | 1 plan template ($20 standing charge), 1 plan, 3 pricing (tiered/flat/stairstep) | Multi-aggregation pricing |
| `app_hosting` | 1 product, 2 meters, 2 aggregations, 1 compound aggregation | 1 plan template, 1 plan, 1 pricing on compound agg | Compound aggregation formula |
| `candidate_checks` | 1 product, 1 meter (segmented fields), 1 segmented aggregation | 1 plan template, 1 plan, 6 segment pricing configs | Segmented aggregation |

#### Evaluators (Weighted Composite)

| Evaluator | Weight | What It Checks |
|-----------|--------|----------------|
| `structural` | 10% | Valid dict, has `name`/`code`, code matches `^[a-z][a-z0-9_]*$`, no empty required fields |
| `schema_compliance` | 20% | Runs MIRA's own `validate_entity()` from `app.validation.engine` — same rules as the real app |
| `completeness` | 15% | Entity count per type vs reference `expected_counts`. Penalty at >150% over-generation |
| `accuracy` | 25% | Fuzzy name matching + key field comparison using Hungarian algorithm (`scipy.linear_sum_assignment`) for optimal 1:1 entity pairing |
| `cross_entity` | 10% | Referential integrity: agg→meter field, pricing→aggregation, accountPlan→account/plan. Checks `approved_*` state keys for WF2/WF3 |
| `semantic` | 20% | LLM-as-Judge (default: claude-opus-4-6) scores 6 dimensions 1-5: relevance, naming, data_model, aggregation_logic, pricing_structure, completeness. Only runs in live mode |

When semantic eval is skipped (no `--judge-model` or mock mode), remaining weights are redistributed proportionally.

#### How It Works

- **Auto-approver**: Runs graphs through HITL `interrupt()` gates by detecting interrupt payloads via `extract_interrupt_payload()` and resuming with approve-all decisions. Max 20 iterations.
- **Graph harness**: Compiles graphs with `MemorySaver` (no Postgres). Mocks Supabase (analysis node use_case fetch, approval DB writes, load_approved entity loading), RAG retrieval, and memory store. Real LLM calls are preserved.
- **Workflow chaining**: WF2 receives approved entities from WF1 output. WF3 receives from both WF1+WF2. The mock `load_approved_entities` returns prior workflow state formatted as Supabase rows.
- **No server needed**: Evals import graph builders directly and run in-process. Only LLM API keys required.

#### Running Evals

**pytest (recommended for individual tests)**:

```bash
cd backend

# Single example, single workflow
pytest evals/test_eval_wf1.py -k "cloud_storage" --model-id claude-sonnet-4-6 -v

# All examples for WF1
pytest evals/test_eval_wf1.py --model-id claude-sonnet-4-6 -v

# Full chain (WF1→WF2→WF3) for one example
pytest evals/test_eval_chain.py -k "app_hosting" --model-id gpt-5.2 -v

# All eval tests
pytest evals/ -m eval_live --model-id claude-sonnet-4-6 -v
```

**pytest CLI options** (defined in `evals/conftest.py`):

| Option | Default | Description |
|--------|---------|-------------|
| `--model-id` | `claude-sonnet-4-6` | Model under test — the LLM that generates billing configs |
| `--eval-mode` | `live` | `live` = real LLM calls, `mock` = replay saved golden responses |
| `--judge-model` | `claude-opus-4-6` | Model used for LLM-as-Judge semantic evaluation |
| `-k "name"` | (all) | pytest filter — use example names: `cloud_storage`, `app_hosting`, `candidate_checks` |

**Standalone CLI** (for multi-model comparison and golden file generation):

```bash
cd backend

# Single model, all workflows
python -m evals.run_eval --model-id claude-sonnet-4-6

# All 6 models (comparison matrix)
python -m evals.run_eval --all-models

# Specific workflow + example
python -m evals.run_eval --workflow wf1 --examples cloud_storage

# Save golden files for mock mode
python -m evals.run_eval --model-id claude-sonnet-4-6 --save-golden

# Custom judge model
python -m evals.run_eval --judge-model gpt-5.2
```

**CLI options** (`python -m evals.run_eval --help`):

| Option | Default | Description |
|--------|---------|-------------|
| `--model-id` | `claude-sonnet-4-6` | Model to evaluate |
| `--all-models` | off | Run across all 6 configured models (claude-sonnet-4-6, claude-opus-4-6, gpt-5.2, gpt-5.4, gemini-3-flash-preview, gemini-3.1-pro-preview) |
| `--examples` | `all` | Comma-separated example names or `all` |
| `--workflow` | `all` | `wf1`, `wf2`, `wf3`, `chain`, or `all` |
| `--judge-model` | `claude-opus-4-6` | Model for LLM-as-Judge semantic evaluation |
| `--save-golden` | off | Save LLM responses as JSON to `evals/golden/` for mock replay |

Results are saved to `evals/golden/latest_results.json` after each CLI run.

#### pytest Markers

- `@pytest.mark.eval` — all eval tests (both live and mock)
- `@pytest.mark.eval_live` — tests requiring real LLM API calls (excluded from CI)
- CI runs `pytest -m "not integration and not eval_live"` to skip both DB and eval tests

## Gotchas

- Backend venv uses Python 3.13 (not 3.14 — hatchling incompatible with 3.14)
- Tailwind v4 uses `@theme inline` blocks in CSS, not `tailwind.config.js`
- shadcn-svelte colors use HSL CSS variables (`--background: 0 0% 100%`) mapped via `@theme` to `--color-*`
- Frontend uses `@sveltejs/adapter-vercel`, not `adapter-auto`
- m3ter has two APIs: Config API (api.m3ter.com) and Ingest API (ingest.m3ter.com)
- Measurements use entity codes (not UUIDs) for submission
- `$lib/utils.ts` is a flat file (not `utils/index.ts`) — shadcn components import `$lib/utils.js` directly and expect `cn`, `WithElementRef`, `WithoutChildrenOrChild`, `WithoutChildren`, `WithoutChild` exports
- shadcn-svelte `components.json` requires `tailwind.baseColor` field (set to `"zinc"`)
- Dark mode uses `mode-watcher` (not manual class toggling) — `ModeWatcher` component in root layout, `toggleMode` for the toggle button
- Never use `supabase.auth.getSession()` alone on the server — always use `safeGetSession()` which calls `getUser()` first to validate the JWT
- Unit tests: Use `TestClient(app)` without `with` (context manager) to avoid triggering the lifespan, which calls `get_db_pool()` and requires a real Postgres connection
- Unit tests: Use `app.dependency_overrides` with `try/finally` to guarantee cleanup — prevents leaked auth overrides between tests
- LangGraph 1.x `graph.ainvoke()` returns normally on `interrupt()` (no exception). Always check `graph.aget_state()` for pending interrupts after `ainvoke()` — never rely solely on catching `GraphInterrupt`. The `except GraphInterrupt: pass` pattern is kept for backward compatibility but the state check is the authoritative source. See `_invoke_and_send_result` in `ws.py` for the canonical pattern.
- Use `from datetime import UTC` (not `timezone.utc`) — ruff UP017 rule enforces this
- Mock Supabase rows for ownership checks must include join data (e.g., `use_cases.projects.user_id`) or queries return 404
