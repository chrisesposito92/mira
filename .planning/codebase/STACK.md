# Technology Stack

**Analysis Date:** 2026-03-22

## Languages

**Primary:**
- Python 3.12+ (requires-python = ">=3.12") — backend FastAPI app, LangGraph agents, RAG pipeline, scripts
- TypeScript 5.9 — entire SvelteKit frontend, strict mode enabled

**Secondary:**
- SQL — Postgres migrations in `backend/migrations/*.sql`
- JSON — shared constants in `shared/constants.json`

## Runtime

**Environment:**
- Node.js 24.13.0 (current system) — frontend dev server and build tooling
- Python 3.12+ (venv at `backend/.venv`) — backend API and agent workflows
  - Note: hatchling build backend is incompatible with Python 3.14; use 3.12 or 3.13

**Package Manager:**
- npm (frontend) — lockfile: `frontend/package-lock.json`, `package-lock.json` (root)
- pip/hatchling (backend) — lockfile: `backend/pyproject.toml` (no separate lockfile)

## Frameworks

**Core (Backend):**
- FastAPI 0.115+ — HTTP API server; entry point `backend/app/main.py`, mounted at port 8000
- Uvicorn (standard extras) — ASGI server with `--reload` for development
- Pydantic v2 10.0+ — all schemas/settings via `BaseSettings` and Pydantic models
- pydantic-settings 2.7+ — settings loaded from `backend/.env` via `backend/app/config.py`

**Core (Frontend):**
- SvelteKit 2.50+ — full-stack framework; `frontend/src/routes/` for routing
- Svelte 5.51+ — component model (uses runes: `$state`, `$derived`, `$effect`; no legacy stores)
- Vite 7.3 — frontend build tool configured in `frontend/vite.config.ts`

**Agent Workflows:**
- LangGraph 0.2+ — StateGraph-based agent workflows; graphs in `backend/app/agents/graphs/`
- LangChain 0.3+ — base abstractions; `init_chat_model()` for multi-provider LLM routing
- langgraph-checkpoint-postgres 2.0+ — `AsyncPostgresSaver` for workflow state persistence
- asyncpg 0.30+ — raw async PostgreSQL driver for checkpointer pool and RAG queries

**Styling:**
- Tailwind CSS v4.2 — configured via `@theme` CSS blocks (no `tailwind.config.js`); Vite plugin via `@tailwindcss/vite`
- shadcn-svelte 1.1 — component library; config at `frontend/components.json` (baseColor: zinc)
- bits-ui 2.16 — headless primitives underlying shadcn-svelte
- mode-watcher 1.1 — dark mode toggle (no manual class toggling)
- lucide-svelte 0.575 — icon set

**Testing (Backend):**
- pytest 8.0+ — test runner; config in `backend/pyproject.toml` (`asyncio_mode = "auto"`)
- pytest-asyncio 0.24+ — async test support
- scipy 1.14+ (dev) — Hungarian algorithm for eval accuracy scoring

**Testing (Frontend):**
- Vitest 4.0 — test runner; config at `frontend/vitest.config.ts` (jsdom environment)
- Testing Library: `@testing-library/svelte`, `@testing-library/user-event`, `@testing-library/jest-dom`

**Build/Dev:**
- `@sveltejs/adapter-vercel` 6.3 — Vercel deployment adapter (not adapter-auto); set in `frontend/svelte.config.js`
- `@sveltejs/vite-plugin-svelte` 6.2 — Svelte Vite integration
- husky 9.1 + lint-staged 16.3 — pre-commit hooks; root `package.json`

## Key Dependencies

**Critical (Backend):**
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

**Critical (Frontend):**
- `@supabase/ssr>=0.8.0` — Supabase SSR client; used in `frontend/src/hooks.server.ts` and layouts
- `@supabase/supabase-js>=2.98.0` — Supabase browser client
- `codemirror>=6.0.2` + `@codemirror/lang-json` + `@codemirror/lint` — JSON editor in `frontend/src/lib/components/control-panel/JsonEditor.svelte`
- `tailwind-merge>=3.5.0` + `clsx>=2.1.1` — `cn()` utility in `frontend/src/lib/utils.ts`
- `svelte-sonner>=1.0.7` — toast notifications

## Configuration

**Environment (Backend):**
- Loaded from `backend/.env` via pydantic-settings `BaseSettings` in `backend/app/config.py`
- Required: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `ENCRYPTION_KEY`, `TAVILY_API_KEY`
- Optional: `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` (defaults to `"mira"`)
- LangSmith vars are explicitly exported to `os.environ` by `backend/app/config.py` at import time

**Environment (Frontend):**
- SvelteKit `$env/static/public` module — prefix `PUBLIC_` for client-exposed vars
- Required: `PUBLIC_SUPABASE_URL`, `PUBLIC_SUPABASE_ANON_KEY`, `PUBLIC_API_URL`, `PUBLIC_WS_URL`

**Build:**
- Backend: `backend/pyproject.toml` (hatchling build system)
- Frontend: `frontend/vite.config.ts`, `frontend/svelte.config.js`, `frontend/tsconfig.json`
- Root scripts: `package.json` delegates to `frontend/` and `backend/` subpackages
- Pre-commit: `package.json` husky hooks run prettier on frontend files and ruff on backend `.py` files

**Linting/Formatting:**
- Backend: Ruff 0.8+ (`select = ["E", "F", "I", "N", "W", "UP"]`, line-length 100); config in `backend/pyproject.toml`
- Frontend: ESLint 10 (`frontend/eslint.config.js`) + Prettier 3.8 (`frontend/.prettierrc`)
  - Prettier: tabs, singleQuote, trailingComma all, printWidth 100, svelte + tailwindcss plugins

## Platform Requirements

**Development:**
- Docker (for local Supabase stack via `docker-compose.yml`)
- Python 3.12 or 3.13 (not 3.14) with venv at `backend/.venv`
- Node.js 24+ for frontend tooling

**Production:**
- Frontend: Vercel (adapter-vercel in `frontend/svelte.config.js`)
- Backend: Any ASGI-compatible host (uvicorn); Supabase for DB and auth
- Database: PostgreSQL 15.8 with `pgvector` and `pgcrypto` extensions (see `backend/migrations/001_extensions.sql`)

---

*Stack analysis: 2026-03-22*
