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

### Test

```bash
npm run test:frontend   # Vitest
npm run test:backend    # Pytest
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
| 4 | Backend core API (CRUD endpoints) | Not started |
| 5+ | Dashboard, scraper/RAG, agent workflows, ... | Not started |

See [docs/ROADMAP.md](docs/ROADMAP.md) for full phase details.
