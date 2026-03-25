# Phase 1: Data Foundation - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend infrastructure — DB schema (diagrams table, component_library table), CRUD API endpoints, component library seed data with pre-fetched logos, and a logo proxy endpoint — so the frontend can persist/retrieve diagrams and browse the component library. Includes adding a top-level "Diagrams" nav link to the sidebar and a minimal diagram list view with create/delete.

**Requirements in scope:** PERS-01, PERS-07, NAV-01, NAV-02, NAV-03, NAV-04, COMP-01, COMP-03, COMP-06

</domain>

<decisions>
## Implementation Decisions

### Component Library Seed Data
- **D-01:** Expanded seed list (~25-30 systems), not just the ~9 m3ter native connectors. Include commonly seen systems in SE diagrams (Snowflake, Segment, HubSpot, Salesforce, Stripe, NetSuite, Zuora, Chargebee, QuickBooks, Xero, Slack, Datadog, Grafana, BigQuery, Redshift, AWS S3, Azure, GCP, Twilio, SendGrid, etc.).
- **D-02:** Systems organized into functional categories (CRM, Billing/Payments, Analytics, Data Warehousing, Messaging, Monitoring, Cloud Infrastructure, etc.) rather than matching m3ter's marketing groupings.
- **D-03:** Seed data lives in a SQL migration file (e.g., `015_seed_component_library.sql`). Adding systems later means a new migration or future admin endpoint.
- **D-04:** Each system has an `is_native_connector` boolean flag to distinguish m3ter native connectors from general systems. This enables Phase 3's CONN-06 (auto-suggest "Native Connector" type when connecting m3ter to a flagged system).

### Logo Proxy Approach
- **D-05:** Logo.dev as the primary logo source. Free tier is 10K requests/month — sufficient when combined with DB caching.
- **D-06:** Logos cached in DB as base64 (column on component_library table). One fetch per system, served from Supabase after that. Eliminates ongoing API rate limit concerns.
- **D-07:** Pre-fetch all seed system logos during the seed process (seed script run after migration). Seed data is complete from day one.
- **D-08:** Monogram fallback (initials on colored background) when Logo.dev returns no result. Matches m3ter's existing diagram style.

### Diagram Data Model
- **D-09:** Single `content` JSONB column on the diagrams table holding systems, connections, positions, and settings. schema_version field governs JSON shape evolution.
- **D-10:** Diagram table fields: `id`, `user_id`, `customer_name`, `title` (for naming flexibility beyond customer_name), `project_id` (nullable FK to projects), `content` (JSONB), `schema_version` (integer, default 1), `thumbnail_base64` (text, nullable — populated by Phase 3), `created_at`, `updated_at`.
- **D-11:** Pydantic model (DiagramContent) defines the JSON content shape in Phase 1 with typed fields: `systems[]`, `connections[]`, `settings{}`. Backend validates on save. Documents the contract for Phase 2's renderer.
- **D-12:** Component library is a full Supabase table (`component_library`) with `id`, `name`, `domain`, `category`, `logo_base64`, `is_native_connector`, `display_order`, `created_at`. Queryable, extensible, allows future admin UI.

### Claude's Discretion
- Exact list of ~25-30 systems and their category assignments — researcher should identify the most common systems SEs encounter
- DiagramContent Pydantic model field names and nesting — planner should design based on Phase 2 renderer needs
- Monogram color assignment strategy (hash-based, category-based, or random)
- Migration numbering (014 for schema, 015 for seed, etc.)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### m3ter Integrations (seed data source)
- `docs.m3ter.com/guides/integrations` — Lists native connector systems; defines which systems get `is_native_connector = true`

### Existing Codebase Patterns
- `backend/migrations/` — Migration 001-013 pattern; next migration starts at 014
- `backend/app/api/router.py` — Central router aggregation; new diagram router registers here
- `backend/app/services/project_service.py` — Reference service layer pattern (sync functions, Supabase client, ownership checks)
- `backend/app/schemas/common.py` — Pydantic schema patterns; EntityType enum for reference
- `frontend/src/lib/components/layout/AppSidebar.svelte` — Sidebar nav items array; add "Diagrams" entry
- `frontend/src/routes/(app)/` — Authenticated route group; new `/diagrams/` route lives here

### Project Documentation
- `.planning/PROJECT.md` — Core constraints (must use existing MIRA stack)
- `.planning/REQUIREMENTS.md` — Full requirement list with phase mapping

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AppSidebar.svelte` — `navItems` array with `{title, url, icon}` objects; add "Diagrams" with a Lucide icon (e.g., `Network` or `GitFork`)
- `ApiClient` class in `services/api.ts` — Base HTTP client with auth headers; new diagram service wraps this
- Factory function pattern (`createXService(client)`) — Use for `createDiagramService()`
- Class-based Svelte 5 store pattern — Use for `DiagramStore` (list, create, delete)
- Existing migration SQL pattern — RLS policies, UUID PKs, `created_at`/`updated_at` timestamps

### Established Patterns
- Backend: Route handler (thin) → Service layer (business logic) → Supabase client
- Backend: `router = APIRouter(prefix="/api/diagrams", tags=["diagrams"])`
- Frontend: `(app)/+layout.server.ts` handles auth guard — new routes under `(app)/diagrams/` get auth for free
- Frontend: Stores export singletons, components consume via import

### Integration Points
- `backend/app/api/router.py` — Register new `diagrams` router
- `backend/app/main.py` — No changes needed (router aggregation handles it)
- `frontend/src/lib/components/layout/AppSidebar.svelte` — Add nav item
- `frontend/src/routes/(app)/` — New `diagrams/` route directory
- `shared/constants.json` — May need diagram-related status enums if applicable

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches following existing codebase patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-data-foundation*
*Context gathered: 2026-03-23*
