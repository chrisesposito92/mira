# MIRA Implementation Roadmap

## Phase Dependency Graph

```
Phase 1 (Scaffold)
  ├── Phase 2 (DB + Auth)
  │     ├── Phase 3 (Frontend Auth)
  │     │     └── Phase 5 (Dashboard) ← also needs Phase 4
  │     │           ├── Phase 8 (Chat UI) ← also needs Phase 7
  │     │           ├── Phase 11 (Control Panel) ← also needs Phase 8
  │     │           └── Phase 13 (Doc Upload) ← also needs Phase 6
  │     ├── Phase 4 (Backend API)
  │     │     ├── Phase 7 (Agent Core) ← also needs Phase 6
  │     │     │     ├── Phase 9 (Plans/Pricing)
  │     │     │     │     └── Phase 10 (Accounts/Usage)
  │     │     │     └── Phase 12 (m3ter Sync) ← also needs Phase 11
  │     │     └── Phase 6 (Scraper + RAG)
  │     └── Phase 6 (needs pgvector)
  Phases 1-13 → Phase 14 (Polish) → Phase 15 (E2E Tests) → Phase 16 (Deploy)
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

- [ ] Enable pgvector extension
- [ ] Migration: `org_connections` table (client_id/secret encrypted, org_id, api_url, connection status)
- [ ] Migration: `projects` table (user_id, org_connection_id FK, customer_name, name, description, default_model_id)
- [ ] Migration: `use_cases` table (project_id FK, title, description, contract_start_date, billing_frequency, currency, target_billing_model, notes, status enum)
- [ ] Migration: `workflows` table (use_case_id FK, workflow_type enum, thread_id, model_id, status enum, interrupt_payload JSONB)
- [ ] Migration: `generated_objects` table (use_case_id FK, entity_type enum, name, code, data JSONB, status enum, validation_errors JSONB, m3ter_id, depends_on UUID[])
- [ ] Migration: `chat_messages` table (workflow_id FK, role enum, content, metadata JSONB)
- [ ] Migration: `documents` table (project_id FK, filename, file_type, storage_path, processing_status, chunk_count)
- [ ] Migration: `embeddings` table (source_type, content, metadata JSONB, embedding vector(1536), project_id nullable)
- [ ] Migration: `profiles` table + trigger on auth.users insert
- [ ] HNSW index on embeddings.embedding column
- [ ] RLS policies on all tables (user can only access own data)
- [ ] Supabase Auth configured (email/password + magic link)
- [ ] **Verify**: Migrations apply cleanly
- [ ] **Verify**: RLS verified (user A can't read user B's data)
- [ ] **Verify**: pgvector accepts vectors
- [ ] **Verify**: Auth signup/login works

---

## Phase 3: Frontend Auth Flow & App Shell

**~25 files** | Depends on: Phase 1, Phase 2

- [ ] `hooks.server.ts` — Supabase SSR auth
- [ ] `hooks.client.ts` — Client-side Supabase init
- [ ] Auth pages: login, register
- [ ] Auth callback handler route
- [ ] App shell: sidebar layout
- [ ] App shell: header with user menu
- [ ] App shell: breadcrumbs
- [ ] Theme toggle (dark mode support)
- [ ] Auth store (Svelte 5 runes)
- [ ] Route guards + redirect logic (unauthenticated → login)
- [ ] **Verify**: Auth store state transitions work
- [ ] **Verify**: Login flow works end-to-end
- [ ] **Verify**: Unauthenticated users redirected to login
- [ ] **Verify**: Dark mode persists across navigation

---

## Phase 4: Backend Core API — CRUD Endpoints

**~35 files** | Depends on: Phase 2

- [ ] Supabase JWT middleware for FastAPI
- [ ] Pydantic models for all entities (org_connections, projects, use_cases, documents, generated_objects, workflows)
- [ ] CRUD routes: org connections (create, list, get, update, delete, test connection)
- [ ] CRUD routes: projects (create, list, get, update, delete)
- [ ] CRUD routes: use cases (create, list, get, update, delete)
- [ ] CRUD routes: documents (upload, list, get, delete)
- [ ] CRUD routes: generated objects (list, get, update status, bulk update)
- [ ] m3ter client wrapper (OAuth2 auth, connection test)
- [ ] Credential encryption (Fernet) for m3ter client_id/secret
- [ ] CORS config for frontend origin
- [ ] **Verify**: Each endpoint tested with httpx TestClient
- [ ] **Verify**: 401 returned without valid JWT
- [ ] **Verify**: RLS enforced through API
- [ ] **Verify**: File upload validation works

---

## Phase 5: Frontend Dashboard & Project Management

**~35 files** | Depends on: Phase 3, Phase 4

- [ ] API client layer (`services/api.ts` base, `services/projects.ts`, `services/use-cases.ts`, etc.)
- [ ] Dashboard page with project grid
- [ ] Project detail page with use case list
- [ ] Create project dialog (name, customer_name, description, org connection, default model)
- [ ] Create use case dialog (title, description, billing_frequency, currency, target_billing_model, contract dates, notes)
- [ ] File upload UI (drag-and-drop) on project page
- [ ] Org connections page (add, test, manage credentials)
- [ ] Project store (Svelte 5 runes)
- [ ] **Verify**: API services work (mocked)
- [ ] **Verify**: Project store reactivity
- [ ] **Verify**: Component rendering
- [ ] **Verify**: Create → navigate → view flow works

---

## Phase 6: m3ter Docs Scraper & Embedding Pipeline

**~20 files** | Depends on: Phase 2, Phase 4

- [ ] `scraper/crawler.py` — Crawl m3ter docs (use llms.txt as manifest), Playwright for JS rendering
- [ ] `rag/chunker.py` — RecursiveCharacterTextSplitter (4000 chars, 200 overlap)
- [ ] `rag/embeddings.py` — OpenAI text-embedding-3-small
- [ ] `rag/ingestion.py` — Pipeline: doc → chunks → embeddings → pgvector
- [ ] `rag/retriever.py` — Two-source cosine similarity search (m3ter docs + user docs)
- [ ] `services/document_processor.py` — PDF/DOCX parsing + chunking + embedding
- [ ] Script: `scripts/scrape_m3ter_docs.py`
- [ ] Script: `scripts/seed_embeddings.py`
- [ ] **Verify**: Scraper fetches pages successfully
- [ ] **Verify**: Chunker splits correctly (size + overlap)
- [ ] **Verify**: Embeddings have correct dimension (1536)
- [ ] **Verify**: RAG returns relevant results for m3ter queries
- [ ] **Verify**: PDF extraction works

---

## Phase 7: LangGraph Agent Core — Products/Meters/Aggregations

**~25 files** | Depends on: Phase 4, Phase 6

- [ ] `agents/graphs/product_meter_agg.py` — Full StateGraph with interrupt() gates
- [ ] `agents/nodes/analysis.py` — Use case analysis (RAG + LLM)
- [ ] `agents/nodes/clarification.py` — Generate clarification questions
- [ ] `agents/nodes/generation.py` — Generate Products, Meters, Aggregations
- [ ] `agents/nodes/validation.py` — Run validation rules on generated objects
- [ ] `agents/nodes/approval.py` — Interrupt for user approval
- [ ] `agents/tools/rag_tool.py` — RAG retrieval tool for agent
- [ ] `agents/tools/m3ter_schema.py` — m3ter schema lookup tool
- [ ] `agents/llm_factory.py` — Multi-model instantiation via init_chat_model()
- [ ] `agents/checkpointer.py` — AsyncPostgresSaver setup
- [ ] `agents/prompts/product_meter.py` — System prompts with m3ter domain knowledge
- [ ] `api/workflows.py` — Start/resume workflow endpoints
- [ ] `api/ws.py` — WebSocket for streaming + interrupt/resume
- [ ] `validation/rules/product.py` — Product validation rules
- [ ] `validation/rules/meter.py` — Meter validation rules
- [ ] `validation/rules/aggregation.py` — Aggregation validation rules
- [ ] **Verify**: Each node works (mocked LLM)
- [ ] **Verify**: State transitions correct through full graph
- [ ] **Verify**: Approval gate pauses and resumes correctly
- [ ] **Verify**: Clarification flow works
- [ ] **Verify**: WebSocket messaging works

---

## Phase 8: Frontend Chat Interface

**~25 files** | Depends on: Phase 5, Phase 7

- [ ] `stores/chat.svelte.ts` — Chat state (messages, streaming, workflow status)
- [ ] `stores/websocket.svelte.ts` — WebSocket connection state
- [ ] `services/websocket.ts` — WebSocket client class (connect, send, receive, reconnect)
- [ ] Component: ChatContainer (message list, auto-scroll)
- [ ] Component: ChatInput (text input, send button)
- [ ] Component: AgentMessage (streaming text with markdown)
- [ ] Component: UserMessage
- [ ] Component: ObjectCard (expandable JSON, Edit/Approve/Reject buttons)
- [ ] Component: ClarificationQuestion (radio options, recommendation highlight, free text)
- [ ] Component: WorkflowStatus (step progress indicator)
- [ ] Component: StreamingIndicator (typing animation)
- [ ] Component: WorkflowLauncher (start workflow, select model)
- [ ] Use case page with chat interface (`routes/(app)/projects/[projectId]/use-cases/[useCaseId]/`)
- [ ] LLM model selector dropdown
- [ ] Connection status indicator
- [ ] **Verify**: Chat store (message append, stream, workflow state)
- [ ] **Verify**: ObjectCard renders with action buttons
- [ ] **Verify**: ClarificationQuestion renders options correctly
- [ ] **Verify**: WebSocket connect/send/receive works
- [ ] **Verify**: Streaming renders smoothly

---

## Phase 9: Plans & Pricing Workflow

**~15 files** | Depends on: Phase 7

- [ ] `agents/graphs/plan_pricing.py` — StateGraph loading approved entities from Workflow 1
- [ ] `agents/nodes/plan_template_gen.py` — PlanTemplate generation
- [ ] `agents/nodes/plan_gen.py` — Plan generation
- [ ] `agents/nodes/pricing_gen.py` — Pricing generation (tiered, volume, stairstep, per-unit, counter)
- [ ] `agents/prompts/plan_pricing.py` — Pricing model knowledge, examples
- [ ] `validation/rules/plan_template.py` — PlanTemplate validation
- [ ] `validation/rules/plan.py` — Plan validation
- [ ] `validation/rules/pricing.py` — Pricing validation (type-specific)
- [ ] **Verify**: Each node works independently
- [ ] **Verify**: All pricing types handled (tiered/volume/stairstep/per-unit/counter)
- [ ] **Verify**: Cross-entity references valid (pricing → plan → template)

---

## Phase 10: Accounts, Usage Data & Remaining Workflows

**~25 files** | Depends on: Phase 9

- [ ] `agents/graphs/account_setup.py` — Form-driven account creation
- [ ] `agents/graphs/usage_submission.py` — Generate measurements, batch, submit to ingest API
- [ ] `validation/rules/account.py` — Account validation
- [ ] `validation/rules/account_plan.py` — AccountPlan validation
- [ ] `validation/rules/measurement.py` — Measurement validation (batch ≤1000, payload ≤512KB)
- [ ] `validation/cross_entity.py` — Full referential integrity checks across all entity types
- [ ] **Verify**: Account references valid plans
- [ ] **Verify**: Usage references valid meters/accounts
- [ ] **Verify**: Batch limits respected (≤1000 measurements, ≤512KB)

---

## Phase 11: Control Panel

**~25 files** | Depends on: Phase 5, Phase 8

- [ ] `stores/objects.svelte.ts` — Tree grouping, selection, sync status
- [ ] Component: ObjectTree (tree hierarchy by entity type)
- [ ] Component: ObjectTreeNode (expandable node with status badge)
- [ ] Component: ObjectEditor (detail panel)
- [ ] Component: JsonEditor (CodeMirror 6 integration)
- [ ] Component: SyncStatusBadge (draft/approved/pushed/failed colors)
- [ ] Component: BulkActions (approve all, push selected, etc.)
- [ ] Component: ManualObjectForm (create object without agent)
- [ ] Control panel page (`routes/(app)/projects/[projectId]/control-panel/`)
- [ ] Toast notifications for sync results
- [ ] **Verify**: Objects store (tree grouping, selection)
- [ ] **Verify**: Tree renders correct hierarchy
- [ ] **Verify**: JSON editor validates on edit
- [ ] **Verify**: Status badges show correct colors

---

## Phase 12: m3ter Push & Sync Integration

**~20 files** | Depends on: Phase 4, Phase 11

- [ ] `m3ter/client.py` — Full SDK wrapper (auth, token caching, CRUD per entity type)
- [ ] `m3ter/entities.py` — Dependency-ordered push, reference resolution (internal UUID → m3ter UUID)
- [ ] `m3ter/mapper.py` — Clean/transform payloads for m3ter API format
- [ ] `api/m3ter_sync.py` — Push, bulk push, status check endpoints
- [ ] WebSocket notifications for sync progress
- [ ] **Verify**: Client methods work (mocked HTTP)
- [ ] **Verify**: Dependency ordering correct (Product before Meter before Aggregation, etc.)
- [ ] **Verify**: Push success/failure handling
- [ ] **Verify**: Reference resolution maps internal→m3ter UUIDs

---

## Phase 13: Document Upload E2E & RAG Enhancement

**~18 files** | Depends on: Phase 5, Phase 6

- [ ] Frontend: Upload progress bar
- [ ] Frontend: File list with delete action
- [ ] Frontend: Drag-and-drop visual feedback
- [ ] Backend: Async document processing (parse → chunk → embed)
- [ ] Backend: Processing status tracking (pending/processing/ready/failed)
- [ ] RAG: Combined m3ter docs + user docs search
- [ ] RAG: Source attribution in retrieved context
- [ ] **Verify**: PDF/DOCX extraction works correctly
- [ ] **Verify**: Upload → chunk → embed → search pipeline works end-to-end
- [ ] **Verify**: Agent receives relevant user doc context in RAG results

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
- [ ] **Verify**: Error/empty states render correctly
- [ ] **Verify**: Keyboard shortcuts work
- [ ] **Verify**: Lighthouse accessibility score >90

---

## Phase 15: E2E Testing Suite

**~30 test files** | Depends on: Phase 14

- [ ] E2E: Auth flow (register, login, logout)
- [ ] E2E: Dashboard (create project, navigate)
- [ ] E2E: Project management (create use case, upload file)
- [ ] E2E: Chat workflow (launch, answer clarification, approve objects)
- [ ] E2E: Control panel (view tree, edit object, push)
- [ ] E2E: Org connections (add, test, delete)
- [ ] Backend integration: Full workflow end-to-end (Workflow 1 → 2 → 3)
- [ ] Backend integration: RAG pipeline (scrape → chunk → embed → retrieve)
- [ ] Backend integration: m3ter sync (push → verify → status)
- [ ] GitHub Actions CI: svelte-check + vitest + pytest + Playwright
- [ ] **Verify**: All E2E tests pass
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
