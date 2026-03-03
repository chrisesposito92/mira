# MIRA Implementation Roadmap

## Phase Dependency Graph

```
Phase 1 (Scaffold)
  ├── Phase 2 (DB + Auth)
  │     ├── Phase 3 (Frontend Auth)
  │     │     └── Phase 3.5 (CI + Testing Infra) ← gates all subsequent PRs
  │     │           └── Phase 5 (Dashboard) ← also needs Phase 4
  │     │                 ├── Phase 8 (Chat UI) ← also needs Phase 7
  │     │                 ├── Phase 11 (Control Panel) ← also needs Phase 8
  │     │                 └── Phase 13 (Doc Upload) ← also needs Phase 6
  │     ├── Phase 4 (Backend API)
  │     │     ├── Phase 7 (Agent Core) ← also needs Phase 6
  │     │     │     ├── Phase 7.5 (Long-Term Memory)
  │     │     │     ├── Phase 9 (Plans/Pricing)
  │     │     │     │     └── Phase 10 (Accounts/Usage)
  │     │     │     └── Phase 12 (m3ter Sync) ← also needs Phase 11
  │     │     └── Phase 6 (Scraper + RAG)
  │     └── Phase 6 (needs pgvector)
  │     │                 └── Phase 13.5 (Use Case Generator) ← also needs Phase 7
  Phases 1-13.5 → Phase 14 (Polish) → Phase 15 (E2E Tests) → Phase 16 (Deploy)
```

**Parallelization**: Phases 3+4 can run in parallel. Phase 6 can start once Phase 2 is done. Phases 4+6 have no dependency on Phase 3.

---

## Phase 0: Roadmap & Architecture Documentation

- [x] Architecture document committed to `docs/`
- [x] Roadmap checklist committed to `docs/`

---

## Phase 1: Monorepo Scaffolding

**~25 files** | Depends on: nothing

- [x] Root `.gitignore` (Python + Node + env + IDE)
- [x] Root `package.json` with workspace scripts
- [x] `shared/constants.json` (entity types, status enums)
- [x] `frontend/` — SvelteKit + TypeScript initialized
- [x] `frontend/` — Tailwind v4 configured (`@tailwindcss/vite`)
- [x] `frontend/` — shadcn-svelte initialized (components.json, CSS variables, `cn()` util)
- [x] `frontend/` — Vercel adapter configured
- [x] `frontend/` — Base directory structure (components, stores, services, types, routes)
- [x] `frontend/.env.example`
- [x] `backend/` — FastAPI + `pyproject.toml` with all dependencies
- [x] `backend/app/main.py` — App factory, lifespan, CORS, `/health` endpoint
- [x] `backend/app/config.py` — Pydantic Settings
- [x] `backend/` — Directory structure for all modules (agents, m3ter, rag, validation, scraper, db)
- [x] `backend/.env.example`
- [x] `docker-compose.yml` — Local Supabase (postgres, auth, rest, meta, studio)
- [x] **Verify**: `npm run build` passes
- [x] **Verify**: `npm run check` passes (0 errors)
- [x] **Verify**: `pytest tests/test_health.py` passes, `/health` returns 200

---

## Phase 2: Supabase Database Schema & Auth

**~12 migration files** | Depends on: Phase 1

- [x] Enable pgvector extension
- [x] Migration: `org_connections` table (client_id/secret encrypted, org_id, api_url, connection status)
- [x] Migration: `projects` table (user_id, org_connection_id FK, customer_name, name, description, default_model_id)
- [x] Migration: `use_cases` table (project_id FK, title, description, contract_start_date, billing_frequency, currency, target_billing_model, notes, status enum)
- [x] Migration: `workflows` table (use_case_id FK, workflow_type enum, thread_id, model_id, status enum, interrupt_payload JSONB)
- [x] Migration: `generated_objects` table (use_case_id FK, entity_type enum, name, code, data JSONB, status enum, validation_errors JSONB, m3ter_id, depends_on UUID[])
- [x] Migration: `chat_messages` table (workflow_id FK, role enum, content, metadata JSONB)
- [x] Migration: `documents` table (project_id FK, filename, file_type, storage_path, processing_status, chunk_count)
- [x] Migration: `embeddings` table (source_type, content, metadata JSONB, embedding vector(1536), project_id nullable)
- [x] Migration: `profiles` table + trigger on auth.users insert
- [x] HNSW index on embeddings.embedding column
- [x] RLS policies on all tables (user can only access own data)
- [x] Supabase Auth configured (email/password + magic link)
- [x] **Verify**: Migrations apply cleanly
- [x] **Verify**: RLS verified (user A can't read user B's data)
- [x] **Verify**: pgvector accepts vectors
- [x] **Verify**: Auth signup/login works

---

## Phase 3: Frontend Auth Flow & App Shell

**~25 files** | Depends on: Phase 1, Phase 2

- [x] `hooks.server.ts` — Supabase SSR auth
- [x] `hooks.client.ts` — Client-side Supabase init
- [x] Auth pages: login, register
- [x] Auth callback handler route
- [x] App shell: sidebar layout
- [x] App shell: header with user menu
- [x] App shell: breadcrumbs
- [x] Theme toggle (dark mode support)
- [x] Auth store (Svelte 5 runes)
- [x] Route guards + redirect logic (unauthenticated → login)
- [ ] **Verify**: Auth store state transitions work
- [ ] **Verify**: Login flow works end-to-end
- [ ] **Verify**: Unauthenticated users redirected to login
- [ ] **Verify**: Dark mode persists across navigation

---

## Phase 3.5: CI, Testing & Linting Infrastructure

**~8 new files, ~8 modified** | Depends on: Phase 3

- [x] Frontend: vitest + @testing-library/svelte + jsdom
- [x] Frontend: eslint + typescript-eslint + eslint-plugin-svelte + prettier
- [x] `frontend/vitest.config.ts` — jsdom env, colocated tests, sveltekit plugin
- [x] `frontend/src/tests/setup.ts` — jest-dom matchers
- [x] `frontend/eslint.config.js` — flat config (svelte + typescript + prettier)
- [x] `frontend/.prettierrc` — tabs, single quotes, 100 width, svelte + tailwindcss plugins
- [x] `frontend/.prettierignore`
- [x] Frontend scripts: `test`, `test:watch`, `lint`, `lint:fix`, `format`
- [x] Seed test: `utils.test.ts` — cn() utility
- [x] Seed test: `auth.svelte.test.ts` — AuthStore class
- [x] Backend: pytest `integration` marker on DB-dependent tests
- [x] `.github/workflows/ci.yml` — frontend + backend parallel jobs
- [x] Prettier baseline formatting applied to all frontend code
- [x] Ruff format baseline applied to all backend code
- [X] **Verify**: `npm run lint` passes
- [X] **Verify**: `npm run test` passes (2 seed tests)
- [X] **Verify**: `npm run build` still works
- [X] **Verify**: `pytest -m "not integration"` passes
- [X] **Verify**: CI workflow triggers and both jobs green

---

## Phase 4: Backend Core API — CRUD Endpoints

**~35 files** | Depends on: Phase 2

- [x] Supabase JWT middleware for FastAPI
- [x] Pydantic models for all entities (org_connections, projects, use_cases, documents, generated_objects, workflows)
- [x] CRUD routes: org connections (create, list, get, update, delete, test connection)
- [x] CRUD routes: projects (create, list, get, update, delete)
- [x] CRUD routes: use cases (create, list, get, update, delete)
- [x] CRUD routes: documents (upload, list, get, delete)
- [x] CRUD routes: generated objects (list, get, update status, bulk update)
- [x] m3ter client wrapper (OAuth2 auth, connection test)
- [x] Credential encryption (Fernet) for m3ter client_id/secret
- [x] CORS config for frontend origin
- **Tests**:
  - [x] API endpoint tests with httpx TestClient + dependency overrides (mock Supabase)
  - [x] Auth middleware tests (valid JWT, expired JWT, missing JWT)
  - [x] Pydantic model validation tests
  - [x] Encryption round-trip test (encrypt → decrypt → verify)
- [x] **Verify**: Each endpoint tested with httpx TestClient
- [x] **Verify**: 401 returned without valid JWT
- [x] **Verify**: RLS enforced through API
- [x] **Verify**: File upload validation works

---

## Phase 5: Frontend Dashboard & Project Management

**~35 files** | Depends on: Phase 3, Phase 4

- [x] API client layer (`services/api.ts` base, `services/projects.ts`, `services/use-cases.ts`, etc.)
- [x] Dashboard page with project grid
- [x] Project detail page with use case list
- [x] Create project dialog (name, customer_name, description, org connection, default model)
- [x] Create use case dialog (title, description, billing_frequency, currency, target_billing_model, contract dates, notes)
- [x] File upload UI (drag-and-drop) on project page
- [x] Org connections page (add, test, manage credentials)
- [x] Project store (Svelte 5 runes)
- **Tests**:
  - [x] API service tests (mock fetch)
  - [x] Project store tests (CRUD state management)
  - [x] Component tests for project/use-case cards
- [x] **Verify**: API services work (mocked)
- [x] **Verify**: Project store reactivity
- [x] **Verify**: Component rendering
- [x] **Verify**: Create → navigate → view flow works

---

## Phase 6: m3ter Docs Scraper & Embedding Pipeline

**~20 files** | Depends on: Phase 2, Phase 4

- [x] `scraper/crawler.py` — Crawl m3ter docs (httpx + llms.txt manifest, rate-limited with semaphore)
- [x] `rag/chunker.py` — RecursiveCharacterTextSplitter (4000 chars, 200 overlap, markdown-aware)
- [x] `rag/embeddings.py` — OpenAI text-embedding-3-small (batched ≤100 per API call)
- [x] `rag/ingestion.py` — Pipeline: doc → chunks → embeddings → pgvector (atomic transactions)
- [x] `rag/retriever.py` — Two-source cosine similarity search (m3ter docs + user docs)
- [x] `services/document_processor.py` — PDF/DOCX/TXT extraction + chunking + embedding
- [x] `services/document_service.py` — Updated: file storage to disk, process_document call, async delete with embedding cleanup
- [x] `schemas/embeddings.py` — RetrievalRequest/RetrievalResult models
- [x] Script: `scripts/scrape_m3ter_docs.py`
- [x] Script: `scripts/seed_embeddings.py`
- **Tests**:
  - [x] Chunker unit tests (size, overlap, boundary handling, markdown splitting)
  - [x] Embedding dimension tests (mock OpenAI, batch splitting)
  - [x] Crawler tests (manifest parsing, page fetch, failure handling)
  - [x] Ingestion tests (chunk+store, delete by type/id)
  - [x] Retriever tests (two-source merge, score ordering, k limit)
  - [x] Document processor tests (PDF/DOCX/TXT extraction, status updates)
- [x] **Verify**: 125 unit tests pass (49 new + 76 existing, 0 regressions)
- [x] **Verify**: Ruff lint + format clean

---

## Phase 7: LangGraph Agent Core — Products/Meters/Aggregations

**~25 files** | Depends on: Phase 4, Phase 6

- [x] `agents/state.py` — WorkflowState TypedDict
- [x] `agents/llm_factory.py` — Multi-model instantiation via init_chat_model() (5 models)
- [x] `agents/checkpointer.py` — AsyncPostgresSaver setup
- [x] `agents/prompts/product_meter.py` — System prompts with m3ter domain knowledge
- [x] `agents/tools/rag_tool.py` — RAG retrieval tool for agent
- [x] `agents/tools/m3ter_schema.py` — Hardcoded m3ter entity schemas
- [x] `agents/nodes/analysis.py` — Use case analysis (RAG + LLM)
- [x] `agents/nodes/clarification.py` — Generate clarification questions with interrupt()
- [x] `agents/nodes/generation.py` — Generate Products, Meters, Aggregations
- [x] `agents/nodes/validation.py` — Run validation rules on generated objects
- [x] `agents/nodes/approval.py` — Interrupt for user approval, persist to DB
- [x] `agents/graphs/product_meter_agg.py` — Full StateGraph with interrupt() gates
- [x] `api/workflows.py` — Start/resume workflow endpoints + GET /api/models
- [x] `api/ws.py` — WebSocket for real-time workflow interaction
- [x] `validation/engine.py` — Validation dispatcher
- [x] `validation/rules/product.py` — Product validation rules
- [x] `validation/rules/meter.py` — Meter validation rules
- [x] `validation/rules/aggregation.py` — Aggregation validation rules
- [x] `schemas/workflows.py` — Extended with WorkflowStart, WorkflowResume, EntityDecision, ClarificationAnswer
- **Tests**:
  - [x] LLM factory tests (registry, list_models, error handling)
  - [x] Validation rule tests per entity type (product, meter, aggregation)
  - [x] Node unit tests (mocked LLM responses)
  - [x] Graph structure tests (nodes, edges, conditional routing)
  - [x] Workflow API endpoint tests (start, resume, auth, models)
- [x] **Verify**: 190 unit tests pass (65 new + 125 existing, 0 regressions)
- [x] **Verify**: Ruff lint + format clean
- [x] **Verify**: Graph compiles and nodes chain correctly
- [x] **Verify**: Validation rules catch all required field/format errors

---

## Phase 8: Frontend Chat Interface

**26 files (22 new, 4 modified)** | Depends on: Phase 5, Phase 7

- [x] `types/workflow.ts` — Workflow, WebSocket, chat, entity, clarification types
- [x] `services/workflow.ts` — REST service (start, get, list, models, messages)
- [x] `services/websocket.ts` — WebSocket client class (connect, send, reconnect with exponential backoff)
- [x] `stores/workflow.svelte.ts` — Unified store (messages, workflow status, WS state, pending interactions)
- [x] `schemas/chat_messages.py` — ChatMessageCreate, ChatMessageResponse Pydantic models
- [x] `services/chat_message_service.py` — list/create messages with ownership check + internal save
- [x] `api/chat_messages.py` — GET/POST /api/workflows/{id}/messages endpoints
- [x] `api/ws.py` — Chat message persistence at 6 WebSocket flow points
- [x] Component: ChatContainer (scrollable message list, auto-scroll)
- [x] Component: ChatMessage (dispatcher — renders per message type)
- [x] Component: EntityCard (expandable JSON, Approve/Edit/Reject buttons)
- [x] Component: EntityEditDialog (modal JSON editor)
- [x] Component: ClarificationCard (radio options, recommendation, free text)
- [x] Component: WorkflowHeader (step progress, connection status dot, model display)
- [x] Component: ThinkingIndicator (animated dots + current step text)
- [x] Component: WorkflowLauncher (model selector + start button)
- [x] Workflow route page (`routes/(app)/projects/[projectId]/use-cases/[useCaseId]/workflow/`)
- [x] UseCaseCard — clickable navigation to workflow route
- **Tests**:
  - [x] Workflow store tests (16 tests — state, messages, WS handlers, decisions)
  - [x] Workflow service tests (6 tests — all REST methods)
  - [x] Chat message API tests (8 tests — GET/POST, auth, ownership)
- [x] **Verify**: 68 frontend tests pass (22 new)
- [x] **Verify**: 198 backend tests pass (8 new)
- [x] **Verify**: svelte-check 0 errors, ESLint 0 errors, Ruff clean

---

## Phase 9: Plans & Pricing Workflow

**~20 files (11 new, 9 modified)** | Depends on: Phase 7

- [x] `agents/state.py` — Extended WorkflowState with 12 new fields for Workflow 2
- [x] `agents/tools/m3ter_schema.py` — PlanTemplate, Plan, Pricing schemas added
- [x] `agents/prompts/plan_pricing.py` — System prompts with pricing model knowledge (5 strategies)
- [x] `agents/nodes/load_approved.py` — Load approved WF1 entities from DB + RAG context
- [x] `agents/nodes/plan_template_gen.py` — PlanTemplate generation node
- [x] `agents/nodes/plan_gen.py` — Plan generation node
- [x] `agents/nodes/pricing_gen.py` — Pricing generation (tiered, volume, stairstep, per-unit, counter)
- [x] `agents/nodes/validation.py` — Fixed step naming bug (rstrip), added 3 new entity entries
- [x] `agents/nodes/approval.py` — Fixed step naming bug, added 3 new entity entries
- [x] `agents/graphs/plan_pricing.py` — Full StateGraph: load → gen → validate → approve (×3 entities)
- [x] `validation/rules/plan_template.py` — PlanTemplate validation (currency, billFrequency, etc.)
- [x] `validation/rules/plan.py` — Plan validation (planTemplateId, overrides)
- [x] `validation/rules/pricing.py` — Pricing validation (pricingBands, type, cumulative, bands ordering)
- [x] `validation/engine.py` — Registered 3 new validators
- [x] `schemas/workflows.py` — Added workflow_type to WorkflowStart
- [x] `services/workflow_service.py` — Parameterized graph selection + WF1 prerequisite check
- [x] `api/ws.py` — Select graph by workflow_type
- [x] `api/workflows.py` — Pass workflow_type to service layer
- [x] Frontend: WorkflowLauncher — Workflow type selector with WF1 prerequisite gating
- [x] Frontend: workflow.svelte.ts, workflow.ts, +page.svelte — Thread workflowType through store/service/route
- **Tests**:
  - [x] Validation rules for plan_template (14 tests), plan (8 tests), pricing (21 tests)
  - [x] Graph structure + node unit tests (22 tests)
  - [x] Workflow service test for workflow_type parameter (1 test)
- [x] **Verify**: 263 backend tests pass (65 new + 198 existing, 0 regressions)
- [x] **Verify**: 70 frontend tests pass (1 new + 69 existing, 0 regressions)
- [x] **Verify**: All pricing types handled (tiered/volume/stairstep/per-unit/counter)
- [x] **Verify**: Ruff lint + format clean, ESLint + Prettier clean

---

## Phase 10: Accounts, Usage Data & Remaining Workflows

**26 files (15 new, 11 modified)** | Depends on: Phase 9

- [x] `agents/state.py` — Extended WorkflowState with 14 new fields for WF3 + WF4
- [x] `agents/tools/m3ter_schema.py` — Account, AccountPlan, Measurement schemas added
- [x] `agents/prompts/account_usage.py` — System prompts for account and measurement generation
- [x] `agents/nodes/load_approved_accounts.py` — Load approved WF1+WF2 entities for WF3
- [x] `agents/nodes/load_approved_usage.py` — Load approved WF1+WF3 entities for WF4
- [x] `agents/nodes/account_gen.py` — Account generation node
- [x] `agents/nodes/account_plan_gen.py` — AccountPlan generation node
- [x] `agents/nodes/measurement_gen.py` — Measurement generation node
- [x] `agents/nodes/validation.py` — Added 3 new entity entries + cross-entity validation integration
- [x] `agents/nodes/approval.py` — Added 3 new entity entries + name fallbacks for AccountPlan/Measurement
- [x] `agents/graphs/account_setup.py` — WF3 StateGraph: load → gen accounts → validate → approve → gen account_plans → validate → approve
- [x] `agents/graphs/usage_submission.py` — WF4 StateGraph: load → gen measurements → validate → approve
- [x] `validation/rules/account.py` — Account validation (name, code, email, currency, address, daysBeforeBillDue)
- [x] `validation/rules/account_plan.py` — AccountPlan validation (accountId, planId, startDate)
- [x] `validation/rules/measurement.py` — Measurement validation (uid, meter, account, ts, data) + batch validation
- [x] `validation/cross_entity.py` — Cross-entity referential integrity (AccountPlan→Account/Plan, Measurement→Meter/Account)
- [x] `validation/engine.py` — Registered 3 new validators
- [x] `services/workflow_service.py` — Added WF3+WF4 graph selection + prerequisite chain (WF1→WF2→WF3→WF4)
- [x] Frontend: WorkflowLauncher — Added WF3 and WF4 buttons with prerequisite gating
- **Tests**:
  - [x] Account + AccountPlan validation tests (22 tests)
  - [x] Measurement validation + batch tests (17 tests)
  - [x] Cross-entity referential integrity tests (11 tests)
  - [x] Account setup graph structure + node tests (16 tests)
  - [x] Usage submission graph structure + node tests (11 tests)
- [x] **Verify**: 342 backend tests pass (77 new + 265 existing, 0 regressions)
- [x] **Verify**: Ruff lint clean, svelte-check 0 errors
- [x] **Verify**: Both new graphs compile correctly
- [x] **Verify**: Prerequisite chain enforced (WF1→WF2→WF3→WF4)

---

## Phase 11: Control Panel

**22 files (12 new, 10 modified)** | Depends on: Phase 5, Phase 8

- [x] `types/api.ts` — GeneratedObject, GeneratedObjectUpdate, BulkStatusUpdate interfaces
- [x] `services/generated-objects.ts` — API client (listObjects, getObject, updateObject, bulkUpdateStatus)
- [x] `stores/objects.svelte.ts` — Tree grouping by entity type (push order), filtering, multi-select, CRUD
- [x] Component: ObjectTree (collapsible tree hierarchy by entity type)
- [x] Component: ObjectTreeNode (node with checkbox, name, status badge)
- [x] Component: ObjectEditor (detail panel with CodeMirror JSON editor, actions)
- [x] Component: JsonEditor (CodeMirror 6 integration with dark mode, linting)
- [x] Component: BulkActions (filter bar + approve/reject selected)
- [x] StatusBadge extended with object statuses (approved, rejected, pushed, push_failed)
- [x] Control panel page (`routes/(app)/projects/[projectId]/use-cases/[useCaseId]/control-panel/`)
- [x] Navigation link from workflow page to control panel
- [x] Toast notifications for update/bulk results
- **Tests**:
  - [x] Generated objects service tests (6 tests)
  - [x] Objects store tests (15 tests — tree grouping, filtering, selection, CRUD)
- [x] **Verify**: All frontend tests pass (~21 new tests)
- [x] **Verify**: svelte-check 0 errors
- [x] **Verify**: ESLint + Prettier clean
- [x] **Verify**: Build succeeds with CodeMirror
- **Deferred**: ManualObjectForm (create objects without the agent) — see Phase 11.5

---

## Phase 12: m3ter Push & Sync Integration

**19 files (10 new, 9 modified)** | Depends on: Phase 4, Phase 11

- [x] `m3ter/client.py` — Full SDK wrapper (auth, token caching with 4h50m TTL, retry logic, CRUD per entity type, Config + Ingest API)
- [x] `m3ter/mapper.py` — Allowlist-based payload mapper (strip internal fields, filter to m3ter-accepted fields, remove nulls)
- [x] `m3ter/entities.py` — Dependency-ordered push engine, ReferenceResolver (internal UUID → m3ter UUID), stop-on-failure chain
- [x] `services/push_service.py` — Push orchestration (single/bulk push, org connection resolution, credential decryption, eligibility checks)
- [x] `api/m3ter_sync.py` — REST endpoints: GET push status, POST single push, POST bulk push
- [x] `schemas/m3ter_sync.py` — Pydantic models for push request/response
- [x] `api/ws.py` — WebSocket `/ws/push/{use_case_id}` endpoint with real-time per-entity progress streaming
- [x] `api/router.py` — m3ter sync router registration
- [x] Frontend: `types/push.ts` — PushWsMessage discriminated union, PushSession, PushObjectProgress, REST response types
- [x] Frontend: `services/generated-objects.ts` — pushObject, pushObjects, getPushStatus methods
- [x] Frontend: `services/push-websocket.ts` — Lightweight PushWebSocketClient (no reconnect)
- [x] Frontend: `stores/objects.svelte.ts` — Push state management (pushSession, pushableSelectedIds, bulk push via WS)
- [x] Frontend: PushProgressPanel component (progress bar, per-entity status icons, dismiss)
- [x] Frontend: PushConfirmDialog component (AlertDialog with entity breakdown, dependency warning)
- [x] Frontend: ObjectEditor — "Push to m3ter" button (green), "Retry Push" for push_failed, enhanced m3ter_id badge
- [x] Frontend: BulkActions — "Push Selected (N)" button with pushable count
- [x] Frontend: ObjectTreeNode — isPushing spinner animation
- [x] Frontend: StatusBadge — pushing status (blue, "Pushing...")
- [x] Frontend: Control panel page — full push flow wiring (single, bulk, confirm dialog, progress panel)
- **Tests**:
  - [x] M3terClient tests (token caching, retry logic, per-entity CRUD — 11 tests)
  - [x] Payload mapper tests (all entity types, field stripping, None removal — 11 tests)
  - [x] ReferenceResolver tests (register/resolve, preload, missing ref error — 6 tests)
  - [x] Push ordering tests (correct sort, stop-on-failure, skip pushed — 7 tests)
  - [x] Push service tests (org resolution, eligibility, ownership — 8 tests)
- [x] **Verify**: 415 backend tests pass (43 new + 372 existing, 0 regressions)
- [x] **Verify**: 95 frontend tests pass (0 regressions)
- [x] **Verify**: svelte-check 0 errors, Ruff lint clean, ESLint + Prettier clean
- [x] **Verify**: Dependency ordering correct (Product → Meter → Aggregation → PlanTemplate → Plan → Pricing → Account → AccountPlan)
- [x] **Verify**: Reference resolution maps internal→m3ter UUIDs with stop-on-failure chain
- [x] **Verify**: Real-time WebSocket push progress streaming works (async on_progress callback)

---

## Phase 13: Document Upload E2E & RAG Enhancement

**~18 files** | Depends on: Phase 5, Phase 6

- [x] Frontend: Upload progress bar (two-phase: HTTP upload % → processing stages)
- [x] Frontend: File list with delete action (existed from Phase 5)
- [x] Frontend: Drag-and-drop visual feedback (enhanced: scale animation, bg-primary/10, file type validation)
- [x] Backend: Async document processing (fire-and-forget via asyncio.create_task)
- [x] Backend: Processing status tracking via WebSocket (extracting → chunking → embedding → storing)
- [x] RAG: Combined m3ter docs + user docs search (existed from Phase 6)
- [x] RAG: Source attribution in retrieved context (existed from Phase 6)
- [x] Backend: Document processing registry (REST → WebSocket bridge)
- [x] Backend: Document WebSocket endpoint (`/ws/documents/{project_id}`)
- [x] Frontend: DocWebSocketClient + XHR upload with progress
- [x] Frontend: ProjectStore integration (uploadProgress state, WS message handling)
- **Tests**:
  - [x] Upload component tests — FileUpload (10 tests), UploadProgressBar (7 tests)
  - [x] Document WebSocket endpoint tests (5 tests: auth, ownership, connection)
  - [x] Processing registry unit tests (6 tests: register/unregister, notify, stale cleanup)
- [x] **Verify**: All backend tests pass (408/408)
- [x] **Verify**: All frontend tests pass (112/112)
- [x] **Verify**: svelte-check 0 errors, eslint + prettier clean, ruff clean

---

## Phase 11.5: Manual Object Creation (Deferred from Phase 11)

**13 files (3 new, 10 modified)** | Depends on: Phase 11

- [x] `schemas/generated_objects.py` — `CreateGeneratedObject` + `GeneratedObjectWithErrors` Pydantic models
- [x] `services/generated_object_service.py` — `create_object()` (validate + insert) + `generate_template()` (schema-driven defaults)
- [x] `api/generated_objects.py` — `POST /api/use-cases/{id}/objects` + `GET /api/objects/templates`
- [x] `types/api.ts` — `CreateObjectPayload` interface
- [x] `services/generated-objects.ts` — `createObject()` + `getTemplates()` methods
- [x] `stores/objects.svelte.ts` — `createObject()` store method (prepend + auto-select)
- [x] Component: CreateObjectDialog (entity type selector, name/code fields, JSON editor with templates)
- [x] Control Panel page — "+ New Object" button, template loading, dialog wiring
- **Tests**:
  - [x] Backend: create endpoint (3 tests), templates endpoint (2 tests)
  - [x] Frontend: service tests (2 tests), store tests (2 tests)
- [x] **Verify**: All backend tests pass (11/11)
- [x] **Verify**: All frontend tests pass (95/95)
- [x] **Verify**: svelte-check 0 errors, ESLint + Prettier clean, Ruff clean

---

## Phase 13.5 — Use Case Generator

**9 files (6 new, 3 modified)** | Depends on: Phase 5, Phase 7

- [x] LangGraph graph with research → clarify → compile flow
- [x] Tavily web search integration for customer research
- [x] Clarification node with interrupt/resume pattern
- [x] Compilation node generating UseCaseCreate-compatible dicts
- [x] Dedicated WebSocket endpoint (`ws://host/ws/generate/{project_id}`)
- [x] REST endpoint for file text extraction
- [x] Multi-step dialog UI (input → progress → clarification → results)
- [x] File upload with in-memory text extraction (PDF/DOCX/TXT)
- [x] Use case result cards with selection and save

---

## Phase 7.5: Long-Term Memory (LangGraph Store)

**3 new files, ~20 modified** | Depends on: Phase 7

- [x] `agents/checkpointer.py` — Shared pool, `get_store()` singleton (`AsyncPostgresStore`), `store.setup()`, pool max_size 10→15
- [x] `agents/state.py` — Added `workflow_history`, `project_memory`, `correction_patterns` memory fields
- [x] `agents/memory.py` — Core memory module: `get_store_from_config()`, namespace helpers, save/load for project context, corrections, workflow history, formatting helpers
- [x] `agents/memory_decisions.py` — UC2: Entity diff engine, preference storage/retrieval (per-user, per-entity-type), weighted pattern classification, prompt formatting
- [x] `agents/memory_rag.py` — UC4: RAG chunk feedback recording (EMA scoring), retrieval, feedback-based re-ranking (0.7×relevance + 0.3×feedback)
- [x] All 5 graph builders wired with `store=` parameter in `compile()`
- [x] UC1: Project-level memory — analysis.py writes context, approval.py captures corrections, generation nodes read memory
- [x] UC2: User decision memory — approval.py computes diffs, stores preferences; all generation nodes retrieve + inject preferences
- [x] UC3: Cross-workflow enrichment — approval.py writes workflow summaries; load_approved_* nodes load history into state
- [x] UC4: RAG feedback — approval.py records chunk signals; rag_tool.py re-ranks with feedback scores
- [x] All prompt templates updated with `{project_memory}`, `{correction_patterns}`, `{user_preferences}`, `{workflow_history}` placeholders
- **Tests**:
  - [x] Memory module tests (24 tests — store access, project context, corrections, workflow history, helpers)
  - [x] Decision memory tests (26 tests — diff engine, preference storage/retrieval, weight progression, formatting)
  - [x] RAG feedback tests (23 tests — hashing, parsing, signal computation, recording, re-ranking)
  - [x] All existing tests updated with `mock_config` fixture (backward compatible)
- [x] **Verify**: 507 backend tests pass (73 new + 434 existing, 0 regressions)
- [x] **Verify**: Ruff lint + format clean

---

## Phase 14: Polish & Error Handling

**~25 files modified** | Depends on: Phases 1–13

- [ ] Global error boundary component
- [ ] Skeleton loaders for all async content
- [ ] Empty state components (no projects, no use cases, no objects)
- [ ] Network failure handling (offline banner, retry)
- [ ] WebSocket auto-reconnection with backoff
- [ ] Form validation (client-side) on all forms
- [ ] Keyboard shortcuts (Cmd+Enter to send, Escape to cancel, etc.)
- [ ] Responsive layout (tablet + desktop)
- [ ] Accessibility audit fixes
- **Tests**:
  - [ ] Error boundary test
  - [ ] Empty state tests
  - [ ] Keyboard shortcut tests
- [ ] **Verify**: Error/empty states render correctly
- [ ] **Verify**: Keyboard shortcuts work
- [ ] **Verify**: Lighthouse accessibility score >90

---

## Phase 15: E2E & Integration Testing

**~20 test files** | Depends on: Phase 14

- [ ] Install `@playwright/test` in frontend
- [ ] `playwright.config.ts` configuration
- [ ] Add Supabase Docker service to CI for integration tests
- [ ] Playwright E2E: Auth flow (register, login, logout)
- [ ] Playwright E2E: Dashboard (create project, navigate)
- [ ] Playwright E2E: Project management (create use case, upload file)
- [ ] Playwright E2E: Chat workflow (launch, answer clarification, approve objects)
- [ ] Playwright E2E: Control panel (view tree, edit object, push)
- [ ] Playwright E2E: Org connections (add, test, delete)
- [ ] Backend integration: Full workflow end-to-end (Workflow 1 → 2 → 3)
- [ ] Backend integration: RAG pipeline (scrape → chunk → embed → retrieve)
- [ ] Backend integration: m3ter sync (push → verify → status)
- [ ] **Verify**: All E2E tests pass
- [ ] **Verify**: All integration tests pass with real Supabase
- [ ] **Verify**: CI pipeline green

---

## Phase 16: Deployment

**~15 files** | Depends on: Phase 15

- [ ] `vercel.json` — Frontend deployment config
- [ ] `Dockerfile` — Backend container
- [ ] `render.yaml` — Render deployment config
- [ ] Production environment variables configured
- [ ] DNS / custom domain setup
- [ ] Health check monitoring
- [ ] `docs/DEPLOYMENT.md` — Deployment runbook
- [ ] **Verify**: Frontend deploys to Vercel
- [ ] **Verify**: Backend deploys to Render
- [ ] **Verify**: WebSocket works in production
- [ ] **Verify**: Auth flow works in production
- [ ] **Verify**: One full workflow tested end-to-end in production
