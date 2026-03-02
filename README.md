# MIRA — Metering Intelligence & Rating Architect

AI-powered m3ter configuration assistant. Analyzes pricing scenarios and auto-generates correct m3ter configurations through guided agent workflows with human-in-the-loop approval gates.

## Tech Stack

- **Backend**: FastAPI + LangGraph (Python)
- **Frontend**: SvelteKit + shadcn-svelte + Tailwind v4 (TypeScript)
- **Database**: Supabase (PostgreSQL + pgvector + Auth + RLS)
- **Auth**: Supabase SSR with cookie-based sessions
- **LLMs**: Multi-model (OpenAI, Anthropic, Google)
- **Deploy**: Vercel (frontend) + Render (backend)

## Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (for local Supabase)

### Setup

```bash
# Frontend
cd frontend && npm install

# Backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Copy env files
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
```

### Run

```bash
# Frontend (from root)
npm run dev:frontend

# Backend (from root)
npm run dev:backend

# Local Supabase
docker compose up -d
```

### Test & Lint

```bash
npm run test:frontend   # Vitest
npm run test:backend    # Pytest (all tests, needs Supabase)
npm run lint:frontend   # ESLint + Prettier
npm run lint:backend    # Ruff
npm run check           # svelte-check
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full details.

## Current Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Architecture & Roadmap docs | Done |
| 1 | Monorepo scaffolding | Done |
| 2 | Database schema, RLS, pgvector, auth config | Done |
| 3 | Frontend auth flow & app shell | Done |
| 3.5 | CI, testing & linting infrastructure | Done |
| 4 | Backend core API (CRUD endpoints) | Done |
| 5 | Frontend dashboard & project management | Done |
| 6 | m3ter docs scraper & RAG embedding pipeline | Done |
| 7 | LangGraph agent core (Products/Meters/Aggregations) | Done |
| 8 | Frontend chat interface (workflow UI, WebSocket, HITL) | Done |
| 9 | Plans & pricing workflow (PlanTemplates, Plans, Pricing) | Done |
| 10 | Accounts, usage data & remaining workflows | Done |
| 11 | Control panel (object tree, JSON editor, bulk actions) | Done |
| 11.5 | Manual object creation (deferred from Phase 11) | Done |
| 12 | m3ter push & sync (dependency-ordered push, real-time WS progress) | Done |
| 13 | Document upload E2E & RAG enhancement | Done |
| 13.5 | AI-powered use case generator (Tavily research, clarification, compilation) | Done |
| 14 | Polish & error handling | Not started |
| 15 | E2E & integration testing | Not started |
| 16 | Deployment | Not started |

See [docs/ROADMAP.md](docs/ROADMAP.md) for full phase details.
