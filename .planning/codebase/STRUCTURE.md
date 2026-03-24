# Codebase Structure

**Analysis Date:** 2026-03-22

## Directory Layout

```
mira/                                    # Monorepo root
├── backend/                             # Python FastAPI + LangGraph backend
│   ├── app/                             # Application package
│   │   ├── main.py                      # FastAPI app factory + lifespan
│   │   ├── config.py                    # Pydantic Settings (pydantic-settings)
│   │   ├── dependencies.py              # FastAPI DI: get_current_user, get_supabase
│   │   ├── api/                         # HTTP/WebSocket route handlers
│   │   │   ├── router.py                # Central APIRouter aggregating all sub-routers
│   │   │   ├── ws.py                    # WebSocket endpoints (workflow, push, docs, gen)
│   │   │   ├── workflows.py             # REST workflow start/resume/list/get
│   │   │   ├── generated_objects.py     # CRUD + push for generated billing objects
│   │   │   ├── projects.py              # Project CRUD
│   │   │   ├── use_cases.py             # Use case CRUD
│   │   │   ├── documents.py             # Document upload + list
│   │   │   ├── chat_messages.py         # Chat history endpoints
│   │   │   ├── org_connections.py       # m3ter org connection management
│   │   │   ├── m3ter_sync.py            # m3ter sync endpoints
│   │   │   └── use_case_generator.py    # Use case generator REST endpoints
│   │   ├── agents/                      # LangGraph agent system
│   │   │   ├── state.py                 # WorkflowState + UseCaseGenState TypedDicts
│   │   │   ├── llm_factory.py           # 6-model registry + get_llm()
│   │   │   ├── checkpointer.py          # AsyncPostgresSaver + AsyncPostgresStore (shared pool)
│   │   │   ├── memory.py                # Long-term store: UC1/UC3 (project, history)
│   │   │   ├── memory_decisions.py      # Long-term store: UC2 (user preferences)
│   │   │   ├── memory_rag.py            # Long-term store: UC4 (RAG feedback EMA)
│   │   │   ├── utils.py                 # extract_interrupt_payload, parse_entity_list
│   │   │   ├── graphs/                  # Compiled StateGraph definitions
│   │   │   │   ├── product_meter_agg.py # WF1: Product, Meter, Aggregation, CompoundAgg
│   │   │   │   ├── plan_pricing.py      # WF2: PlanTemplate, Plan, Pricing
│   │   │   │   ├── account_setup.py     # WF3: Account, AccountPlan
│   │   │   │   ├── usage_submission.py  # WF4: Measurement
│   │   │   │   └── use_case_gen.py      # Use case generator graph (MemorySaver)
│   │   │   ├── nodes/                   # Async node functions for graph steps
│   │   │   │   ├── analysis.py          # analyze_use_case (fetch DB + RAG + LLM)
│   │   │   │   ├── clarification.py     # generate_clarifications (interrupt)
│   │   │   │   ├── generation.py        # generate_products/meters/aggregations
│   │   │   │   ├── plan_template_gen.py # generate_plan_templates
│   │   │   │   ├── plan_gen.py          # generate_plans
│   │   │   │   ├── pricing_gen.py       # generate_pricing (5 strategies)
│   │   │   │   ├── account_gen.py       # generate_accounts
│   │   │   │   ├── account_plan_gen.py  # generate_account_plans
│   │   │   │   ├── measurement_gen.py   # generate_measurements
│   │   │   │   ├── validation.py        # validate_entities (dispatches by current_step)
│   │   │   │   ├── approval.py          # approve_entities (interrupt + DB persist)
│   │   │   │   ├── load_approved.py     # Load WF1 approved entities for WF2
│   │   │   │   ├── load_approved_accounts.py  # Load WF1+WF2 for WF3
│   │   │   │   ├── load_approved_usage.py     # Load WF1+WF3 for WF4
│   │   │   │   ├── use_case_research.py  # Tavily web search + LLM summary
│   │   │   │   ├── use_case_clarify.py   # Use case gen clarification (interrupt)
│   │   │   │   └── use_case_compile.py   # Compile research into UseCaseCreate dicts
│   │   │   ├── prompts/                 # LLM system prompts
│   │   │   │   ├── product_meter.py     # WF1 prompts (analysis, product, meter, agg)
│   │   │   │   ├── plan_pricing.py      # WF2 prompts (plan template, plan, pricing)
│   │   │   │   ├── account_usage.py     # WF3+WF4 prompts (account, account plan, measurement)
│   │   │   │   └── use_case_gen.py      # Use case generator prompts
│   │   │   └── tools/                   # Agent tools
│   │   │       ├── rag_tool.py          # RAG retrieval wrapper for nodes
│   │   │       └── m3ter_schema.py      # Hardcoded m3ter entity schemas (all 10 types)
│   │   ├── auth/                        # JWT verification
│   │   │   └── jwt.py                   # verify_token(), AuthError
│   │   ├── db/                          # Database client singletons
│   │   │   └── client.py                # get_supabase_client(), get_db_pool()
│   │   ├── m3ter/                       # m3ter API integration
│   │   │   ├── client.py                # M3terClient (OAuth2, retry, token cache)
│   │   │   ├── mapper.py                # Allowlist-based MIRA→m3ter payload mapper
│   │   │   ├── entities.py              # PUSH_ORDER, ReferenceResolver, push_entities_ordered()
│   │   │   └── encryption.py            # Fernet credential encryption/decryption
│   │   ├── rag/                         # RAG pipeline
│   │   │   ├── chunker.py               # Text chunking
│   │   │   ├── embeddings.py            # OpenAI text-embedding-3-small batch embedding
│   │   │   ├── ingestion.py             # Chunk+embed+store pipeline
│   │   │   └── retriever.py             # Two-source cosine similarity retrieval
│   │   ├── schemas/                     # Pydantic v2 models + shared StrEnums
│   │   │   └── common.py                # EntityType, ObjectStatus, WorkflowType, WorkflowStatus, etc.
│   │   ├── scraper/                     # m3ter docs crawler
│   │   ├── services/                    # Business logic layer
│   │   │   ├── workflow_service.py      # Graph start/resume, prerequisite enforcement
│   │   │   ├── push_service.py          # m3ter push orchestration
│   │   │   ├── generated_object_service.py
│   │   │   ├── document_service.py      # Upload + extract text
│   │   │   ├── document_processor.py    # Async chunk+embed pipeline
│   │   │   ├── document_processing_registry.py  # WebSocket observer registry
│   │   │   ├── chat_message_service.py
│   │   │   ├── project_service.py
│   │   │   ├── use_case_service.py
│   │   │   └── org_connection_service.py
│   │   └── validation/                  # Entity validation
│   │       ├── engine.py                # validate_entity() dispatcher
│   │       ├── common.py                # validate_name, validate_code, shared helpers
│   │       ├── cross_entity.py          # Referential integrity checks
│   │       └── rules/                   # Per-entity rule modules (10 files)
│   │           ├── product.py
│   │           ├── meter.py
│   │           ├── aggregation.py
│   │           ├── compound_aggregation.py
│   │           ├── plan_template.py
│   │           ├── plan.py
│   │           ├── pricing.py
│   │           ├── account.py
│   │           ├── account_plan.py
│   │           └── measurement.py
│   ├── evals/                           # Evaluation system (LLM-as-Judge)
│   │   ├── datasets/                    # 3 reference billing config examples
│   │   ├── evaluators/                  # 6 weighted evaluators (structural, schema, etc.)
│   │   ├── runner/                      # Auto-approver + graph harness + workflow chain
│   │   ├── golden/                      # Saved golden LLM responses for mock mode
│   │   ├── test_eval_wf1.py             # pytest evals WF1
│   │   ├── test_eval_wf2.py             # pytest evals WF2
│   │   ├── test_eval_wf3.py             # pytest evals WF3
│   │   ├── test_eval_chain.py           # Full WF1→WF2→WF3 chain eval
│   │   └── run_eval.py                  # Standalone CLI eval runner
│   ├── migrations/                      # SQL migrations (001–013)
│   ├── scripts/                         # Utility scripts
│   │   ├── scrape_m3ter_docs.py         # Scrape m3ter docs → JSON
│   │   └── seed_embeddings.py           # Seed pgvector from scraped JSON
│   ├── tests/                           # pytest unit + integration tests
│   ├── data/m3ter_docs/                 # Scraped m3ter docs JSON (gitignored?)
│   ├── uploads/                         # Uploaded user documents (UUID subdirs)
│   └── pyproject.toml                   # Python deps + ruff config
├── frontend/                            # SvelteKit TypeScript frontend
│   ├── src/
│   │   ├── app.d.ts                     # SvelteKit type augmentations (locals, PageData)
│   │   ├── hooks.server.ts              # Server hook: Supabase SSR client + safeGetSession
│   │   ├── hooks.client.ts              # Client hook
│   │   ├── routes/                      # SvelteKit file-based routing
│   │   │   ├── +layout.svelte           # Root layout (ModeWatcher, Toaster, auth subscription)
│   │   │   ├── +layout.ts               # Universal layout load (Supabase browser/server client)
│   │   │   ├── +layout.server.ts        # Pass session/user/cookies to layout
│   │   │   ├── +page.svelte             # Root redirect page
│   │   │   ├── (auth)/                  # Unauthenticated routes (centered layout)
│   │   │   │   ├── login/               # Login page
│   │   │   │   └── register/            # Register page
│   │   │   ├── (app)/                   # Authenticated routes (sidebar layout)
│   │   │   │   ├── +layout.server.ts    # Auth guard → redirect to /login
│   │   │   │   ├── dashboard/           # Dashboard page
│   │   │   │   ├── orgs/                # Org connections page
│   │   │   │   └── projects/[projectId]/
│   │   │   │       ├── +page.svelte     # Project detail (use case list)
│   │   │   │       └── use-cases/[useCaseId]/
│   │   │   │           └── control-panel/  # Primary use case view
│   │   │   │               └── +page.svelte  # ObjectTree + ObjectEditor + WorkflowDrawer
│   │   │   └── auth/
│   │   │       └── confirm/+server.ts   # Supabase email confirm callback
│   │   └── lib/
│   │       ├── utils.ts                 # cn(), snakeToTitle, other shared utils
│   │       ├── components/
│   │       │   ├── ui/                  # shadcn-svelte base components (alert, badge, button, etc.)
│   │       │   ├── chat/                # Workflow chat UI
│   │       │   │   ├── ChatContainer.svelte
│   │       │   │   ├── ChatMessage.svelte       # Dispatcher → EntityCard | ClarificationCard | etc.
│   │       │   │   ├── EntityCard.svelte         # Entity approval card with approve/edit/reject
│   │       │   │   ├── ClarificationCard.svelte  # Clarification question card
│   │       │   │   ├── EntityEditDialog.svelte
│   │       │   │   ├── WorkflowHeader.svelte
│   │       │   │   └── ThinkingIndicator.svelte
│   │       │   ├── control-panel/       # Main use case management UI
│   │       │   │   ├── ObjectTree.svelte          # Entity tree (grouped by type, collapsible)
│   │       │   │   ├── ObjectTreeNode.svelte       # Single tree node with status + push spinner
│   │       │   │   ├── ObjectEditor.svelte         # Right panel: JSON editor + push button
│   │       │   │   ├── JsonEditor.svelte           # CodeMirror 6 JSON editor
│   │       │   │   ├── BulkActions.svelte          # Toolbar: bulk status, push selected
│   │       │   │   ├── CreateObjectDialog.svelte   # Manual object creation modal
│   │       │   │   ├── PushConfirmDialog.svelte    # AlertDialog before bulk push
│   │       │   │   ├── PushProgressPanel.svelte    # Real-time push progress
│   │       │   │   ├── WorkflowDrawer.svelte       # Sheet drawer wrapping chat
│   │       │   │   ├── WorkflowLauncherDropdown.svelte  # Workflow type + model selector
│   │       │   │   └── UseCaseMetadataPanel.svelte
│   │       │   ├── project/             # Project/use case management UI
│   │       │   │   ├── ProjectCard.svelte
│   │       │   │   ├── UseCaseCard.svelte
│   │       │   │   ├── CreateProjectDialog.svelte
│   │       │   │   ├── CreateUseCaseDialog.svelte
│   │       │   │   ├── CreateOrgConnectionDialog.svelte
│   │       │   │   ├── OrgConnectionCard.svelte
│   │       │   │   ├── FileUpload.svelte            # Drag-drop + XHR progress upload
│   │       │   │   ├── UploadProgressBar.svelte     # Two-phase: upload% → stage indicators
│   │       │   │   ├── GenerateUseCasesDialog.svelte  # Use case generator multi-step dialog
│   │       │   │   ├── UseCaseResultCard.svelte     # Generated use case result with select
│   │       │   │   ├── StatusBadge.svelte
│   │       │   │   └── EmptyState.svelte
│   │       │   └── layout/              # App shell components
│   │       │       ├── AppSidebar.svelte
│   │       │       ├── AppHeader.svelte
│   │       │       ├── Breadcrumbs.svelte
│   │       │       ├── ThemeToggle.svelte
│   │       │       └── UserMenu.svelte
│   │       ├── stores/                  # Svelte 5 runes class-based stores
│   │       │   ├── workflow.svelte.ts   # WorkflowStore (WS + HITL + chat)
│   │       │   ├── objects.svelte.ts    # ObjectsStore (object list + push session)
│   │       │   ├── project.svelte.ts    # ProjectStore (projects + upload progress)
│   │       │   ├── auth.svelte.ts       # AuthStore (session, user, profile)
│   │       │   └── org-connections.svelte.ts
│   │       ├── services/                # HTTP + WebSocket client wrappers
│   │       │   ├── api.ts               # Base ApiClient (fetch wrapper + auth headers)
│   │       │   ├── workflow.ts          # createWorkflowService() — REST start/resume/list
│   │       │   ├── websocket.ts         # WebSocketClient (auto-reconnect, exponential backoff)
│   │       │   ├── generated-objects.ts # createGeneratedObjectService() — CRUD + push
│   │       │   ├── push-websocket.ts    # PushWebSocketClient (no reconnect)
│   │       │   ├── doc-websocket.ts     # DocWebSocketClient (passive observer)
│   │       │   ├── generator-websocket.ts  # GeneratorWebSocketClient
│   │       │   ├── simple-websocket.ts
│   │       │   ├── projects.ts
│   │       │   ├── use-cases.ts
│   │       │   ├── documents.ts
│   │       │   └── org-connections.ts
│   │       └── types/                   # TypeScript type definitions
│   │           ├── index.ts             # Re-exports all types
│   │           ├── api.ts               # Core domain types (Project, UseCase, GeneratedObject, etc.)
│   │           ├── auth.ts              # UserProfile
│   │           ├── workflow.ts          # ChatMessage discriminated union + WS message types
│   │           ├── push.ts              # Push session + progress types
│   │           ├── document.ts          # Document processing stage types
│   │           └── generator.ts         # Use case generator WS message types
│   ├── static/                          # Static assets
│   └── package.json                     # Frontend deps (SvelteKit, Tailwind v4, shadcn-svelte)
├── shared/
│   └── constants.json                   # Canonical enums: entityTypes, objectStatuses, workflowTypes, etc.
├── supabase/                            # Supabase local dev config
├── docs/                                # Project documentation
│   ├── ARCHITECTURE.md                  # Full architecture doc
│   ├── ROADMAP.md                       # Phase checklist
│   └── PLAN.md                          # Implementation plan
├── docker-compose.yml                   # Local Supabase (postgres:54322, auth:54321, studio:54323)
├── package.json                         # Root npm scripts (dev:frontend, dev:backend, etc.)
└── AGENTS.md                            # Primary project instructions for Claude
```

## Directory Purposes

**`backend/app/api/`:**
- Purpose: FastAPI route handlers only — no business logic
- Contains: One router module per domain resource; `ws.py` for all WebSocket endpoints; `router.py` aggregates everything
- Key files: `backend/app/api/ws.py` (4 WebSocket endpoints), `backend/app/api/workflows.py` (REST workflow lifecycle), `backend/app/api/router.py`

**`backend/app/agents/`:**
- Purpose: Complete LangGraph agent system — state, graphs, nodes, prompts, memory, tools
- Contains: Everything needed to define and run the 4 billing config workflows + use case generator
- Key files: `backend/app/agents/state.py` (all workflow state), `backend/app/agents/graphs/` (5 compiled graphs), `backend/app/agents/nodes/approval.py` (HITL gate), `backend/app/agents/llm_factory.py`

**`backend/app/m3ter/`:**
- Purpose: Complete m3ter API integration — auth, entity push, payload transformation
- Contains: Client with OAuth2 + retry, allowlist mapper, reference resolver, credential encryption
- Key files: `backend/app/m3ter/client.py`, `backend/app/m3ter/entities.py` (push engine), `backend/app/m3ter/mapper.py`

**`backend/app/validation/rules/`:**
- Purpose: One validation module per m3ter entity type; all return `list[ValidationError]`
- Contains: 10 files named exactly after the entity type (e.g. `meter.py`, `pricing.py`)
- Key files: `backend/app/validation/engine.py` (dispatcher), `backend/app/validation/cross_entity.py`

**`backend/evals/`:**
- Purpose: Standalone evaluation harness — runs workflows with real LLMs and scores output; never imports from `api/`
- Contains: datasets (3 reference examples), evaluators (6 weighted), runner (auto-approver + graph harness)
- Key files: `backend/evals/run_eval.py`, `backend/evals/runner/graph_harness.py`

**`backend/migrations/`:**
- Purpose: Sequential SQL migration files applied to Supabase
- Contains: 13 numbered SQL files (001–013)
- Key files: `backend/migrations/008_generated_objects.sql`, `backend/migrations/007_workflows.sql`

**`frontend/src/routes/(app)/`:**
- Purpose: All authenticated pages; guarded by `(app)/+layout.server.ts` session check
- Contains: `dashboard/`, `orgs/`, `projects/[projectId]/use-cases/[useCaseId]/control-panel/`
- Key files: `frontend/src/routes/(app)/projects/[projectId]/use-cases/[useCaseId]/control-panel/+page.svelte` (primary use case view)

**`frontend/src/lib/stores/`:**
- Purpose: Svelte 5 runes class-based state stores; exported as singletons from `index.ts`
- Contains: 5 store files (`.svelte.ts` extension required for runes)
- Key files: `frontend/src/lib/stores/workflow.svelte.ts`, `frontend/src/lib/stores/objects.svelte.ts`

**`shared/`:**
- Purpose: Single source of truth for enumeration values shared between backend and frontend
- Contains: `constants.json` only
- Key files: `shared/constants.json`

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI app creation and lifespan management
- `frontend/src/hooks.server.ts`: SvelteKit server hook (Supabase SSR init)
- `frontend/src/routes/+layout.svelte`: Root SvelteKit layout

**Configuration:**
- `backend/app/config.py`: Pydantic Settings (all env vars with defaults)
- `frontend/src/app.d.ts`: SvelteKit locals and PageData type augmentations
- `shared/constants.json`: Canonical enum values for both packages

**Core Logic:**
- `backend/app/agents/state.py`: All workflow state definitions
- `backend/app/agents/nodes/approval.py`: HITL interrupt/resume gate
- `backend/app/agents/nodes/validation.py`: Entity validation dispatch
- `backend/app/m3ter/entities.py`: Push order and reference resolution
- `backend/app/services/workflow_service.py`: Workflow lifecycle orchestration

**Testing:**
- `backend/tests/`: pytest unit + integration tests
- `backend/evals/`: LLM evaluation harness (separate from unit tests)
- `frontend/src/lib/` (colocated): `*.test.ts` files alongside components and stores

## Naming Conventions

**Backend Files:**
- Route handlers: `{resource}.py` (e.g., `projects.py`, `workflows.py`, `ws.py` for WebSocket)
- Service modules: `{resource}_service.py` (e.g., `workflow_service.py`, `push_service.py`)
- Node modules: `{entity}_gen.py` for generation nodes (e.g., `plan_gen.py`, `pricing_gen.py`); descriptive names for shared nodes (`approval.py`, `validation.py`, `analysis.py`)
- Validation rules: Exactly the entity type name (e.g., `meter.py`, `compound_aggregation.py`)
- Graph modules: `{workflow_name}.py` (e.g., `product_meter_agg.py`, `plan_pricing.py`)

**Frontend Files:**
- Components: `PascalCase.svelte` (e.g., `EntityCard.svelte`, `WorkflowDrawer.svelte`)
- Stores: `kebab-case.svelte.ts` (e.g., `workflow.svelte.ts`, `objects.svelte.ts`)
- Services: `kebab-case.ts` (e.g., `generated-objects.ts`, `push-websocket.ts`)
- Types: `kebab-case.ts` (e.g., `workflow.ts`, `push.ts`)
- Tests (colocated): `ComponentName.svelte.test.ts` or `module-name.test.ts`

**Directories:**
- Backend: `snake_case/` (e.g., `generated_objects/`, `use_case_generator/`)
- Frontend: `kebab-case/` (e.g., `control-panel/`, `use-cases/`)
- Frontend routes: SvelteKit file-based routing with `[paramName]` dynamic segments and `(group)` layout groups

## Where to Add New Code

**New m3ter entity type:**
- Validation rule: `backend/app/validation/rules/{entity_type}.py` (implement `validate(data: dict) -> list[ValidationError]`)
- Register in engine: `backend/app/validation/engine.py`
- m3ter schema: `backend/app/agents/tools/m3ter_schema.py` (add `{ENTITY}_SCHEMA` dict)
- Mapper allowlist: `backend/app/m3ter/mapper.py` (`_ALLOWED_FIELDS` dict)
- Push client method: `backend/app/m3ter/client.py`
- Push order: `backend/app/m3ter/entities.py` (`PUSH_ORDER` list)
- Shared constants: `shared/constants.json` (`entityTypes` array)
- Frontend types: `frontend/src/lib/types/index.ts` (`EntityType` union)

**New API endpoint:**
- Create: `backend/app/api/{resource}.py` (FastAPI `APIRouter`)
- Register: `backend/app/api/router.py`
- Service logic: `backend/app/services/{resource}_service.py`
- Schemas: `backend/app/schemas/` (Pydantic v2 request/response models)

**New workflow graph (additional WF):**
- State fields: `backend/app/agents/state.py` (extend `WorkflowState`)
- Graph: `backend/app/agents/graphs/{workflow_name}.py`
- Register: `backend/app/services/workflow_service.py` (`get_graph()`, `_SUPPORTED_WORKFLOW_TYPES`)
- Node functions: `backend/app/agents/nodes/{entity}_gen.py`
- Prompts: `backend/app/agents/prompts/{topic}.py`

**New frontend page:**
- Route file: `frontend/src/routes/(app)/{path}/+page.svelte`
- Server load (if auth needed): `frontend/src/routes/(app)/{path}/+page.server.ts`
- Components: `frontend/src/lib/components/{feature}/ComponentName.svelte`
- Colocated test: `frontend/src/lib/components/{feature}/ComponentName.svelte.test.ts`

**New Svelte store:**
- File: `frontend/src/lib/stores/{name}.svelte.ts`
- Export: Add to `frontend/src/lib/stores/index.ts`

**New API service (frontend):**
- File: `frontend/src/lib/services/{resource}.ts` (use factory function pattern: `createXService(client)`)
- Export: Add to `frontend/src/lib/services/index.ts`

**Utility functions:**
- Backend: `backend/app/agents/utils.py` (agent utilities) or module-level helpers in the relevant package
- Frontend: `frontend/src/lib/utils.ts` (must export `cn` — shadcn components depend on it)

## Special Directories

**`backend/.venv/`:**
- Purpose: Python virtual environment (Python 3.13)
- Generated: Yes
- Committed: No

**`backend/evals/golden/`:**
- Purpose: Saved LLM responses for mock eval mode; `latest_results.json` written after each CLI run
- Generated: Yes (by `--save-golden` flag)
- Committed: No (not committed — gitignored)

**`backend/uploads/`:**
- Purpose: Uploaded user documents stored in UUID-named subdirectories
- Generated: Yes
- Committed: No

**`backend/data/m3ter_docs/`:**
- Purpose: Scraped m3ter documentation JSON (input for `seed_embeddings.py`)
- Generated: Yes (by `python -m scripts.scrape_m3ter_docs`)
- Committed: No

**`.planning/`:**
- Purpose: GSD planning documents (codebase maps, phase plans)
- Generated: Yes (by GSD commands)
- Committed: Yes

**`.worktrees/`:**
- Purpose: Git worktrees for parallel feature development
- Generated: Yes
- Committed: No

**`supabase/`:**
- Purpose: Supabase local dev configuration (used with `docker compose up -d`)
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-03-22*
