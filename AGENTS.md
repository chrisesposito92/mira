# MIRA — Metering Intelligence & Rating Architect

AI-powered m3ter configuration assistant. Generates correct m3ter billing configs through LangGraph agent workflows with human-in-the-loop approval gates.

## Commands

```bash
# Root-level (from /mira)
npm run dev:frontend          # SvelteKit dev server on :5173
npm run dev:backend           # FastAPI on :8000 (uvicorn --reload)
npm run build                 # Build frontend (Vercel adapter)
npm run check                 # svelte-check TypeScript validation
npm run test:frontend         # Vitest
npm run test:backend          # pytest (run from backend/ with venv active)
npm run lint:backend          # ruff check
npm run format:backend        # ruff format

# Backend (must activate venv first)
cd backend && source .venv/bin/activate
pytest tests/ -v              # Run all backend tests
pytest tests/test_health.py   # Single test file

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
| `agents/` | LangGraph StateGraphs, nodes, prompts, tools |
| `auth/` | Supabase JWT verification |
| `db/` | Supabase client, repository pattern |
| `m3ter/` | m3ter SDK wrapper, entity push, auth |
| `rag/` | Embeddings, chunking, retrieval |
| `scraper/` | Playwright docs crawler |
| `services/` | Business logic layer |
| `validation/` | Per-entity validators + cross-entity checks |

### Frontend Structure (`frontend/src/`)

| Directory | Purpose |
|-----------|---------|
| `lib/components/ui/` | shadcn-svelte base components |
| `lib/components/chat/` | Chat UI (AgentMessage, ObjectCard, etc.) |
| `lib/components/control-panel/` | Object tree, JSON editor |
| `lib/components/project/` | Project/use case cards |
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
- **Entity push order**: Product → Meter → Aggregation → CompoundAgg → PlanTemplate → Plan → Pricing → Account → AccountPlan
- **m3ter auth**: OAuth2 client credentials per org, tokens cached 5hrs
- **RAG**: Two-source retrieval (m3ter docs + user docs), pgvector cosine similarity
- **Checkpointing**: LangGraph AsyncPostgresSaver, resume by thread_id

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
`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `ENCRYPTION_KEY`

### Frontend (`frontend/.env`)
`PUBLIC_SUPABASE_URL`, `PUBLIC_SUPABASE_ANON_KEY`, `PUBLIC_API_URL`, `PUBLIC_WS_URL`

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
