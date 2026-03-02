# MIRA — Metering Intelligence & Rating Architect

## Context

m3ter is a powerful but complex billing/metering platform. Solution architects need to configure Meters, Aggregations, Plans, Pricing, Accounts, and more before a single bill generates. Misconfiguration causes 1-3% revenue leakage. MIRA is an AI-powered assistant that analyzes pricing scenarios and auto-generates correct m3ter configurations through guided agent workflows with human-in-the-loop approval gates.

**Users**: Internal m3ter solution architects (small team, simple auth)

---

## Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Agent Framework | **LangGraph (Python)** | Purpose-built for sequential chains with interrupt() HITL, Postgres checkpointing, multi-model |
| Backend | **FastAPI (Python)** | m3ter Python SDK, LangGraph native, complex schema validation |
| Frontend | **SvelteKit (TypeScript)** | Lightweight, fast, excellent DX |
| UI Components | **shadcn-svelte** | Tailwind-based, copy-paste ownership, great for data-heavy UI |
| Database/Auth | **Supabase** | PostgreSQL + pgvector + Auth + Storage in one |
| Vector Storage | **Supabase pgvector** | Same DB, no extra service |
| Scraper | **Python + Playwright** | Port of Zuora scraper pattern, consistent with backend |
| Deploy (backend) | **Render** | Docker, background workers, WebSocket support |
| Deploy (frontend) | **Vercel** | SvelteKit adapter, preview deploys |
| LLMs | **Multi-model via LangChain** | GPT-5.2, Claude Opus/Sonnet 4.6, Gemini 3 Flash/Pro |

---

## Monorepo Structure

```
mira/
├── backend/                    # Python (FastAPI + LangGraph)
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py             # FastAPI app factory, lifespan, CORS
│   │   ├── config.py           # Pydantic Settings
│   │   ├── dependencies.py     # DI: auth, DB, m3ter client
│   │   ├── auth/               # Supabase JWT verification
│   │   ├── api/                # FastAPI routes
│   │   │   ├── projects.py, use_cases.py, workflows.py
│   │   │   ├── objects.py, m3ter_sync.py, documents.py
│   │   │   └── ws.py           # WebSocket endpoint
│   │   ├── services/           # Business logic
│   │   ├── agents/             # LangGraph workflows
│   │   │   ├── checkpointer.py # AsyncPostgresSaver
│   │   │   ├── llm_factory.py  # Multi-model instantiation
│   │   │   ├── prompts/        # System prompts per workflow
│   │   │   ├── graphs/         # StateGraph definitions
│   │   │   ├── nodes/          # Shared node implementations
│   │   │   └── tools/          # RAG retrieval, m3ter lookup
│   │   ├── m3ter/              # SDK wrapper, auth, entity push
│   │   ├── rag/                # Embeddings, chunker, retriever
│   │   ├── validation/         # Per-entity schema validators
│   │   │   ├── engine.py
│   │   │   ├── rules/          # product.py, meter.py, pricing.py, etc.
│   │   │   └── cross_entity.py # Referential integrity checks
│   │   ├── scraper/            # Playwright m3ter docs crawler
│   │   └── db/                 # Supabase client, repositories
│   ├── scripts/                # scrape_m3ter_docs.py, seed_embeddings.py
│   ├── migrations/             # SQL migration files
│   └── tests/
├── frontend/                   # SvelteKit (TypeScript)
│   ├── src/
│   │   ├── hooks.server.ts     # Supabase SSR auth
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   │   ├── ui/         # shadcn-svelte components
│   │   │   │   ├── chat/       # ChatContainer, AgentMessage, ObjectCard, ClarificationQuestion, etc.
│   │   │   │   ├── control-panel/  # ObjectTree, JsonEditor, SyncStatusBadge, BulkActions
│   │   │   │   ├── project/    # ProjectCard, UseCaseCard, FileUpload
│   │   │   │   └── layout/     # AppSidebar, Header, Breadcrumbs
│   │   │   ├── stores/         # Svelte 5 runes ($state-based)
│   │   │   ├── services/       # API client layer
│   │   │   ├── types/          # TypeScript type definitions
│   │   │   └── utils/
│   │   └── routes/
│   │       ├── (auth)/         # Login, register (centered layout)
│   │       └── (app)/          # Authenticated routes (sidebar layout)
│   │           ├── dashboard/
│   │           ├── projects/[projectId]/
│   │           │   ├── use-cases/[useCaseId]/  # Chat interface
│   │           │   ├── control-panel/          # Object tree + editor
│   │           │   └── settings/
│   │           └── orgs/       # Org connection management
│   └── tests/
├── shared/                     # Shared constants (entity types, status enums)
└── docs/                       # Architecture, plans
```

---

## Database Schema (Key Tables)

**`org_connections`** — m3ter org credentials (client_id/secret encrypted, org_id, api_url, connection status)

**`projects`** — user_id, org_connection_id FK, customer_name, name, description, default_model_id

**`use_cases`** — project_id FK, title, description, contract_start_date, billing_frequency, currency, target_billing_model, notes, status (draft/in_progress/completed)

**`workflows`** — use_case_id FK, workflow_type enum, thread_id (LangGraph), model_id, status (pending/running/interrupted/completed/failed), interrupt_payload JSONB

**`generated_objects`** — use_case_id FK, entity_type enum, name, code, data JSONB, status (draft/approved/rejected/pushed/push_failed), validation_errors JSONB, m3ter_id, depends_on UUID[]

**`chat_messages`** — workflow_id FK, role (user/assistant/system), content, metadata JSONB

**`documents`** — project_id FK, filename, file_type, storage_path, processing_status, chunk_count

**`embeddings`** — source_type (m3ter_docs/user_document), content, metadata JSONB, embedding vector(1536), project_id (null for global m3ter docs)

All tables have RLS policies scoped to user ownership. LangGraph checkpoint tables auto-created by AsyncPostgresSaver.

---

## Agent Workflows

### Shared Architecture
- **Shared State**: TypedDict flowing through entire graph — all nodes read/write same state (use case context, RAG chunks, generated objects, user decisions, conversation history)
- **Checkpointing**: AsyncPostgresSaver (Postgres) — auto-persists at every node boundary, resume by thread_id
- **HITL Pattern**: `interrupt()` at approval gates → serializes state → WebSocket sends interrupt payload to frontend → user approves/edits/rejects → `Command(resume=decision)` continues graph
- **Clarification Questions**: 2-4 multiple choice options + free text + LLM recommendation, rendered as ClarificationQuestion component in chat
- **Model Selection**: User picks model per-workflow; `llm_factory.get_llm(model_id)` instantiates via `init_chat_model()`
- **RAG**: Two-source retrieval (m3ter docs + user-uploaded docs), merged by similarity score

### Workflow 1: Products / Meters / Aggregations
```
START → analyze_use_case (RAG + LLM) → ask_clarifications (interrupt if needed)
→ generate_products → validate → approve_products (interrupt)
→ generate_meters → validate → approve_meters (interrupt)
→ generate_aggregations → validate → approve_aggregations (interrupt) → END
```
Rejection loops back to the generate step with user feedback.

### Workflow 2: PlanTemplates / Plans / Pricing
```
START → load_approved_entities (from Workflow 1)
→ generate_plan_templates → validate → approve (interrupt)
→ generate_plans → validate → approve (interrupt)
→ generate_pricing → validate → approve (interrupt) → END
```
Handles tiered, volume, stairstep, per-unit, and counter pricing.

### Workflow 3: Accounts / AccountPlans
More form-driven, less LLM. User provides account details.
```
START → suggest_accounts (LLM) → approve_account_config (interrupt: form)
→ validate → suggest_account_plans → approve (interrupt) → END
```

### Workflow 4: Usage Submission
```
START → analyze_meters → configure_usage (interrupt: user specifies volume/dates)
→ generate_measurements → validate (batch ≤1000, payload ≤512KB)
→ approve_submission (interrupt: preview) → submit_batches (ingest API) → report → END
```

---

## Agent UX: Full Chat Interface

Everything happens in a conversational thread. Custom message types:
- **AgentMessage** — streaming text with markdown
- **UserMessage** — text input
- **ObjectCard** — expandable JSON card with Edit/Approve/Reject buttons
- **ClarificationQuestion** — radio options, highlighted recommendation, free text fallback
- **WorkflowStatus** — step progress indicator
- **StreamingIndicator** — typing animation

Real-time via WebSocket (one per workflow session). Event protocol includes: status updates, streaming tokens, generated objects, validation results, interrupt payloads.

**Control Panel** is a separate page: tree view of all objects → click to edit JSON → bulk push to m3ter.

---

## m3ter Integration

- **Auth**: OAuth2 Client Credentials (client_id + client_secret per org) → JWT token
- **SDK**: m3ter-sdk-python wraps all API calls
- **Push ordering**: Product → Meter → Aggregation → CompoundAgg → PlanTemplate → Plan → Pricing → Account → AccountPlan
- **Reference resolution**: Internal UUIDs mapped to m3ter UUIDs during push (id_mapping dict)
- **Ingest**: Measurements POST to ingest.m3ter.com (separate domain), uses codes not UUIDs

---

## Phased Implementation Roadmap

### Phase 0: Roadmap & Architecture Documentation
**Output**: This plan document + detailed architecture doc committed to `docs/`
**Tests**: N/A (documentation only)

---

### Phase 1: Monorepo Scaffolding
**What**: Set up monorepo with SvelteKit frontend + FastAPI backend, all tooling
**Deliverables**:
- Root monorepo: `.gitignore`, root `package.json` (workspace scripts)
- `frontend/`: SvelteKit + TypeScript + Tailwind + shadcn-svelte initialized, Vercel adapter, base components installed
- `backend/`: FastAPI + pyproject.toml, `app/main.py` health endpoint, `app/config.py` Pydantic Settings
- `.env.example` files for both
- Docker Compose for local dev (Supabase local)
**Tests**: `npm run build` passes, `npm run check` passes, uvicorn starts, `/health` returns 200
**~25 files**

---

### Phase 2: Supabase Database Schema & Auth
**What**: All migration files, RLS policies, pgvector extension, Supabase Auth config
**Depends on**: Phase 1
**Deliverables**:
- Migration files for all tables (org_connections, projects, use_cases, workflows, generated_objects, chat_messages, documents, embeddings)
- RLS policies (user can only access own data)
- pgvector extension enabled, HNSW index on embedding column
- Supabase Auth configured for email/password + magic link
- Profiles table with trigger on auth.users
**Tests**: Migrations apply clean, RLS verified (user A can't read user B's data), pgvector accepts vectors, auth signup/login works
**~12 migration files**

---

### Phase 3: Frontend Auth Flow & App Shell
**What**: Supabase SSR auth in SvelteKit, login/register pages, authenticated app shell with sidebar
**Depends on**: Phase 1, Phase 2
**Deliverables**:
- `hooks.server.ts` (Supabase SSR), `hooks.client.ts`
- Auth pages: login, register, callback handler
- App shell: sidebar, header, breadcrumbs, theme toggle, user menu
- Auth store, route guards, redirect logic
- Dark mode support
**Tests**: Auth store state transitions, login flow, unauthenticated redirect, dark mode persists
**~25 files**

---

### Phase 4: Backend Core API — CRUD Endpoints
**What**: FastAPI routes for projects, use cases, org connections, documents, objects
**Depends on**: Phase 2
**Deliverables**:
- Supabase JWT middleware for FastAPI
- Pydantic models for all entities
- CRUD routes: orgs, projects, use_cases, documents, objects
- m3ter client wrapper (auth, connection test)
- Credential encryption (Fernet)
- CORS config
**Tests**: Each endpoint tested (httpx TestClient), 401 without JWT, RLS enforced, file upload validation
**~35 files**

---

### Phase 5: Frontend Dashboard & Project Management
**What**: Dashboard, project detail, use case creation, org connections, file upload UI
**Depends on**: Phase 3, Phase 4
**Deliverables**:
- API client layer (`services/api.ts`, `services/projects.ts`, etc.)
- Dashboard page with project grid
- Project detail with use case list, file upload (drag-and-drop), settings
- Create project/use case dialogs with all fields (including billing_frequency, currency, target_billing_model)
- Org connections page (add, test, manage)
- Project store
**Tests**: API services (mocked), project store, component rendering, create-navigate-view flow
**~35 files**

---

### Phase 6: m3ter Docs Scraper & Embedding Pipeline
**What**: Playwright scraper for docs.m3ter.com, chunking, embedding generation, RAG retrieval
**Depends on**: Phase 2, Phase 4
**Deliverables**:
- `scraper/crawler.py` — crawl m3ter docs (use llms.txt as manifest), Playwright for JS rendering
- `rag/chunker.py` — RecursiveCharacterTextSplitter (4000 chars, 200 overlap)
- `rag/embeddings.py` — OpenAI text-embedding-3-small
- `rag/ingestion.py` — Pipeline: doc → chunks → embeddings → pgvector
- `rag/retriever.py` — Two-source cosine similarity search (m3ter docs + user docs)
- `services/document_processor.py` — PDF/DOCX parsing + chunking + embedding
- Scripts: `scrape_m3ter_docs.py`, `seed_embeddings.py`
**Tests**: Scraper fetches pages, chunker splits correctly, embeddings correct dimension, RAG returns relevant results, PDF extraction works
**~20 files**

---

### Phase 7: LangGraph Agent Core — Products/Meters/Aggregations
**What**: First agent workflow: analyze use case → generate Products → Meters → Aggregations with approval gates
**Depends on**: Phase 4, Phase 6
**Deliverables**:
- `agents/graphs/product_meter_agg.py` — full StateGraph with interrupt() gates
- `agents/nodes/` — analysis, generation, validation, clarification, approval nodes
- `agents/tools/` — RAG retrieval tool, m3ter schema tool
- `agents/llm_factory.py` — multi-model via init_chat_model()
- `agents/checkpointer.py` — AsyncPostgresSaver setup
- `agents/prompts/product_meter.py` — system prompts with m3ter domain knowledge
- `api/workflows.py` — start/resume endpoints
- `api/ws.py` — WebSocket for streaming + interrupt/resume
- Validation rules: `validation/rules/product.py`, `meter.py`, `aggregation.py`
**Tests**: Each node (mocked LLM), state transitions, approval gate pauses/resumes, clarification flow, WebSocket messaging
**~25 files**

---

### Phase 8: Frontend Chat Interface
**What**: Full chat UI with streaming, object cards, clarification questions, WebSocket integration
**Depends on**: Phase 5, Phase 7
**Deliverables**:
- `stores/chat.svelte.ts`, `stores/websocket.svelte.ts`
- `services/websocket.ts` — WebSocket client class
- Chat components: ChatContainer, ChatInput, AgentMessage, UserMessage, ObjectCard, ClarificationQuestion, WorkflowStatus, StreamingIndicator, WorkflowLauncher
- Use case page with chat interface
- LLM model selector dropdown
- Connection status indicator
**Tests**: Chat store (message append, stream, workflow state), ObjectCard renders/buttons, ClarificationQuestion renders options, WebSocket connect/send/receive, streaming renders smoothly
**~25 files**

---

### Phase 9: Plans & Pricing Workflow
**What**: Second agent workflow: PlanTemplates → Plans → Pricing (tiered/volume/stairstep/counter)
**Depends on**: Phase 7
**Deliverables**:
- `agents/graphs/plan_pricing.py` — StateGraph loading approved entities from Workflow 1
- `agents/nodes/` — plan template generation, plan generation, pricing generation (handles all pricing types)
- `agents/prompts/plan_pricing.py` — pricing model knowledge, tiered vs volume examples
- Validation: `validation/rules/plan_template.py`, `plan.py`, `pricing.py`
**Tests**: Each node, pricing type handling (tiered/volume/stairstep), cross-entity references valid
**~15 files**

---

### Phase 10: Accounts, Usage Data & Remaining Workflows
**What**: Account/AccountPlan setup (form-driven) + Usage submission agent
**Depends on**: Phase 9
**Deliverables**:
- `agents/graphs/account_setup.py` — form-driven account creation
- `agents/graphs/usage_submission.py` — generate measurements, batch, submit to ingest API
- Validation: `validation/rules/account.py`, `account_plan.py`, `measurement.py`
- `validation/cross_entity.py` — full referential integrity checks
**Tests**: Account references valid plans, usage references valid meters/accounts, batch limits respected
**~25 files**

---

### Phase 11: Control Panel
**What**: Object tree view, JSON editor, sync status, bulk actions, manual object creation
**Depends on**: Phase 5, Phase 8
**Deliverables**:
- `stores/objects.svelte.ts` — tree grouping, selection, sync status
- Components: ObjectTree, ObjectTreeNode, ObjectEditor, JsonEditor (CodeMirror 6), SyncStatusBadge, BulkActions, ManualObjectForm
- Control panel page with tree hierarchy
- Toast notifications for sync results
**Tests**: Objects store (tree/selection), tree renders hierarchy, JSON editor validates, status badges correct colors
**~25 files**

---

### Phase 12: m3ter Push & Sync Integration
**What**: Actual m3ter API integration — push objects in dependency order, sync status tracking
**Depends on**: Phase 4, Phase 11
**Deliverables**:
- `m3ter/client.py` — full SDK wrapper (auth, token caching, CRUD per entity)
- `m3ter/entities.py` — dependency-ordered push, reference resolution (internal→m3ter UUIDs)
- `m3ter/mapper.py` — clean/transform payloads for m3ter API
- `api/m3ter_sync.py` — push, bulk push, status check endpoints
- WebSocket notifications for sync progress
**Tests**: Client methods (mocked HTTP), dependency ordering, push success/failure handling, reference resolution
**~20 files**

---

### Phase 13: Document Upload E2E & RAG Enhancement
**What**: Complete file upload flow + user doc RAG integration + source attribution
**Depends on**: Phase 5, Phase 6
**Deliverables**:
- Frontend: upload progress bar, file list with delete, drag-and-drop feedback
- Backend: async document processing (parse → chunk → embed), processing status tracking
- RAG: combined m3ter docs + user docs search, source attribution in context
**Tests**: PDF/DOCX extraction, upload→chunk→embed→search pipeline, agent gets relevant user doc context
**~18 files**

---

### Phase 13.5: Use Case Generator
**What**: AI-powered use case generation from customer research — a hybrid LangGraph graph with Tavily web search, clarification questions, and a dedicated WebSocket endpoint
**Depends on**: Phase 5, Phase 7
**Deliverables**:
- LangGraph graph (`graphs/use_case_gen.py`) with `UseCaseGenState` (separate from `WorkflowState`), using `MemorySaver` (not `AsyncPostgresSaver`)
- Three nodes: `research_customer` (Tavily web search), `ask_clarification` (interrupt/resume), `compile_use_cases` (generate `UseCaseCreate`-compatible dicts)
- Prompts: `prompts/use_case_gen.py` — research and compilation system prompts
- Dedicated WebSocket endpoint: `ws://host/ws/generate/{project_id}` with protocol messages: `gen_status`, `gen_clarification`, `gen_use_cases`, `gen_error`
- REST endpoint: `POST /api/projects/{project_id}/generate-use-cases/extract-text` for in-memory file text extraction (PDF/DOCX/TXT)
- Frontend: `GenerateUseCasesDialog.svelte` — multi-step dialog (input → progress → clarification → results), `UseCaseResultCard.svelte` for result display
- Frontend: `services/generator-websocket.ts` (WebSocket client), `types/generator.ts` (TypeScript types)
**Tests**: Graph structure, node unit tests, WebSocket endpoint auth, file extraction
**~9 files (6 new, 3 modified)**

---

### Phase 14: Polish & Error Handling
**What**: Loading states, empty states, error boundaries, keyboard shortcuts, accessibility
**Depends on**: Phases 1-13
**Deliverables**: Global error boundary, skeleton loaders, empty states, network failure handling, WebSocket reconnection, form validation, keyboard shortcuts, responsive layout, accessibility audit
**Tests**: Error/empty states render, keyboard shortcuts work, Lighthouse accessibility >90
**~25 files modified**

---

### Phase 15: E2E Testing Suite
**What**: Playwright E2E tests + backend integration tests + CI pipeline
**Depends on**: Phase 14
**Deliverables**:
- E2E: auth, dashboard, project, chat, control-panel, orgs flows
- Backend integration: full workflow e2e, RAG pipeline, m3ter sync
- GitHub Actions CI: svelte-check, vitest, pytest, Playwright
**~30 test files**

---

### Phase 16: Deployment
**What**: Vercel (frontend) + Render (backend) deployment, production config
**Depends on**: Phase 15
**Deliverables**: vercel.json, Dockerfile, render.yaml, production env vars, DNS, health checks, DEPLOYMENT.md
**Tests**: Both deploy, WebSocket works in prod, auth flow works, one full workflow tested
**~15 files**

---

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

**Parallelization opportunities**: Phases 3+4 can run in parallel (frontend auth + backend API). Phase 6 can start once Phase 2 is done (independent of Phase 3). Phases 4+6 have no dependency on Phase 3.

---

## Verification

After each phase:
1. All tests pass (`pytest` for backend, `vitest` + `svelte-check` for frontend)
2. No TypeScript errors, no Python linting errors
3. Manual smoke test of new functionality
4. Git commit with passing CI

End-to-end verification (Phase 15+):
1. Create account → login → create org connection → test connection
2. Create project → create use case → upload pricing sheet
3. Launch Workflow 1 → answer clarification → approve Products → approve Meters → approve Aggregations
4. Launch Workflow 2 → approve PlanTemplates → approve Plans → approve Pricing
5. Launch Workflow 3 → create Accounts → assign AccountPlans
6. Control Panel → view tree → edit object → push to m3ter → verify sync status
7. Launch Workflow 4 → generate usage → submit to m3ter ingest
8. Verify objects exist in m3ter org via API/dashboard
