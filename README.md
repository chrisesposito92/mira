# MIRA — Metering Intelligence & Rating Architect

AI-powered m3ter configuration assistant. Analyzes pricing scenarios and auto-generates correct m3ter configurations through guided agent workflows with human-in-the-loop approval gates. Also includes a branded integration architecture diagram builder for Solutions Engineers.

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
- Node.js 24+
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

## Features

### AI Billing Configuration
LangGraph agent workflows with human-in-the-loop approval that generate complete m3ter billing configurations (Products, Meters, Aggregations, Plans, Pricing, Accounts). Includes multi-model support, RAG retrieval from m3ter docs, and a control panel for reviewing/editing/pushing entities to m3ter.

### Integration Architecture Diagrammer (v1.0)
Configurator-style diagram builder for m3ter SEs to assemble branded integration architecture diagrams:
- **Component Library**: 29 pre-seeded native connector systems organized by category, plus custom system nodes with logo fetch
- **Live Preview**: Pure SVG rendering with m3ter branding (navy background, white cards, green accent, color-coded connections)
- **Configurator UI**: Three-tab builder with SystemPicker, ConnectionForm with native connector auto-suggest, auto-save
- **Export**: PNG (2x HiDPI) and SVG with inlined Inter font and pre-fetched base64 logos

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full details.
