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
│   │   │   │   ├── chat/       # ChatContainer, AgentMessage, ObjectCard, etc.
│   │   │   │   ├── control-panel/  # ObjectTree, JsonEditor, SyncStatusBadge
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
- **Shared State**: TypedDict flowing through entire graph — all nodes read/write same state
- **Checkpointing**: AsyncPostgresSaver (Postgres) — auto-persists at every node boundary
- **HITL Pattern**: `interrupt()` at approval gates → serializes state → WebSocket sends interrupt payload to frontend → user approves/edits/rejects → `Command(resume=decision)` continues graph
- **Clarification Questions**: 2-4 multiple choice + free text + LLM recommendation
- **Model Selection**: User picks model per-workflow; `llm_factory.get_llm(model_id)` instantiates via `init_chat_model()`
- **RAG**: Two-source retrieval (m3ter docs + user-uploaded docs), merged by similarity score

### Workflow 1: Products / Meters / Aggregations
```
START → analyze_use_case → ask_clarifications (interrupt if needed)
→ generate_products → validate → approve_products (interrupt)
→ generate_meters → validate → approve_meters (interrupt)
→ generate_aggregations → validate → approve_aggregations (interrupt) → END
```

### Workflow 2: PlanTemplates / Plans / Pricing
```
START → load_approved_entities
→ generate_plan_templates → validate → approve (interrupt)
→ generate_plans → validate → approve (interrupt)
→ generate_pricing → validate → approve (interrupt) → END
```

### Workflow 3: Accounts / AccountPlans
```
START → suggest_accounts → approve_account_config (interrupt: form)
→ validate → suggest_account_plans → approve (interrupt) → END
```

### Workflow 4: Usage Submission
```
START → analyze_meters → configure_usage (interrupt)
→ generate_measurements → validate
→ approve_submission (interrupt: preview) → submit_batches → report → END
```

---

## m3ter Integration

- **Auth**: OAuth2 Client Credentials (client_id + client_secret per org) → JWT token
- **SDK**: m3ter-sdk-python wraps all API calls
- **Push ordering**: Product → Meter → Aggregation → CompoundAgg → PlanTemplate → Plan → Pricing → Account → AccountPlan
- **Reference resolution**: Internal UUIDs mapped to m3ter UUIDs during push
- **Ingest**: Measurements POST to ingest.m3ter.com (separate domain), uses codes not UUIDs

---

## Phased Implementation

See individual phase documents for detailed implementation plans.

Phases 0-16 covering: scaffolding → DB schema → auth → API → dashboard → scraper/RAG → agent core → chat UI → plans/pricing → accounts/usage → control panel → m3ter sync → doc upload → polish → E2E tests → deployment.
