# Phase 1: Data Foundation - Research

**Researched:** 2026-03-23
**Domain:** Backend CRUD infrastructure (SQL migrations, FastAPI endpoints, Pydantic schemas), component library seed data with logo fetching, frontend sidebar nav + minimal list view
**Confidence:** HIGH

## Summary

Phase 1 establishes the persistence and API layer for the diagram builder feature. The work is entirely additive -- new tables, new endpoints, new frontend route -- with zero changes to existing MIRA functionality. Every pattern needed (SQL migrations with RLS, FastAPI route/service/schema layering, Svelte 5 runes stores, factory service functions) is already proven in the codebase across 13 migrations and 10 API route modules.

The two novel elements are: (1) a JSONB `content` column validated by a nested Pydantic model (DiagramContent), and (2) a logo proxy endpoint that fetches from Logo.dev and caches as base64. Both are straightforward -- Pydantic v2 (2.12.5 installed) handles nested model serialization natively for JSONB, and httpx (0.28.1 already installed) handles the external Logo.dev fetch.

**Primary recommendation:** Clone the `projects` module pattern (migration, schemas, service, API, frontend service/store/route) for `diagrams`, add a separate `component_library` table with seed data, and add a `/api/logos/proxy` endpoint using httpx to fetch from Logo.dev with DB caching.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Expanded seed list (~25-30 systems), not just the ~9 m3ter native connectors. Include commonly seen systems in SE diagrams (Snowflake, Segment, HubSpot, Salesforce, Stripe, NetSuite, Zuora, Chargebee, QuickBooks, Xero, Slack, Datadog, Grafana, BigQuery, Redshift, AWS S3, Azure, GCP, Twilio, SendGrid, etc.).
- **D-02:** Systems organized into functional categories (CRM, Billing/Payments, Analytics, Data Warehousing, Messaging, Monitoring, Cloud Infrastructure, etc.) rather than matching m3ter's marketing groupings.
- **D-03:** Seed data lives in a SQL migration file (e.g., `015_seed_component_library.sql`). Adding systems later means a new migration or future admin endpoint.
- **D-04:** Each system has an `is_native_connector` boolean flag to distinguish m3ter native connectors from general systems. This enables Phase 3's CONN-06 (auto-suggest "Native Connector" type when connecting m3ter to a flagged system).
- **D-05:** Logo.dev as the primary logo source. Free tier is 10K requests/month -- sufficient when combined with DB caching.
- **D-06:** Logos cached in DB as base64 (column on component_library table). One fetch per system, served from Supabase after that. Eliminates ongoing API rate limit concerns.
- **D-07:** Pre-fetch all seed system logos during the seed process (seed script run after migration). Seed data is complete from day one.
- **D-08:** Monogram fallback (initials on colored background) when Logo.dev returns no result. Matches m3ter's existing diagram style.
- **D-09:** Single `content` JSONB column on the diagrams table holding systems, connections, positions, and settings. schema_version field governs JSON shape evolution.
- **D-10:** Diagram table fields: `id`, `user_id`, `customer_name`, `title` (for naming flexibility beyond customer_name), `project_id` (nullable FK to projects), `content` (JSONB), `schema_version` (integer, default 1), `thumbnail_base64` (text, nullable -- populated by Phase 3), `created_at`, `updated_at`.
- **D-11:** Pydantic model (DiagramContent) defines the JSON content shape in Phase 1 with typed fields: `systems[]`, `connections[]`, `settings{}`. Backend validates on save. Documents the contract for Phase 2's renderer.
- **D-12:** Component library is a full Supabase table (`component_library`) with `id`, `name`, `domain`, `category`, `logo_base64`, `is_native_connector`, `display_order`, `created_at`. Queryable, extensible, allows future admin UI.

### Claude's Discretion
- Exact list of ~25-30 systems and their category assignments -- researcher should identify the most common systems SEs encounter
- DiagramContent Pydantic model field names and nesting -- planner should design based on Phase 2 renderer needs
- Monogram color assignment strategy (hash-based, category-based, or random)
- Migration numbering (014 for schema, 015 for seed, etc.)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PERS-01 | User can save a diagram to Supabase with a customer name | Diagrams table with `customer_name` field; CRUD API endpoints cloning project pattern |
| PERS-07 | Diagram data model includes schema_version field for future migration safety | `schema_version INTEGER NOT NULL DEFAULT 1` on diagrams table |
| NAV-01 | Top-level "Diagrams" section in the sidebar navigation | Add entry to `navItems` array in `AppSidebar.svelte` with `Network` icon |
| NAV-02 | Diagram optionally linked to an existing MIRA Project | `project_id UUID REFERENCES projects(id) ON DELETE SET NULL` nullable FK |
| NAV-03 | User can create a new diagram from the Diagrams section | CreateDiagramDialog component + POST endpoint |
| NAV-04 | User can delete a diagram | DELETE endpoint + DeleteDiagramDialog component |
| COMP-01 | Pre-populated system nodes for all m3ter native connectors with company logos | `component_library` table seeded with ~28 systems; m3ter native connectors flagged with `is_native_connector = true` |
| COMP-03 | Systems organized into grouped categories | `category` column on component_library; seed data assigns functional categories |
| COMP-06 | Backend logo proxy endpoint to convert external logos to base64 | `/api/logos/proxy?domain=X` endpoint using httpx to fetch from Logo.dev, returns base64 |
</phase_requirements>

## Standard Stack

### Core (already installed -- no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.133.1 | HTTP API server | Already the backend framework |
| Pydantic v2 | 2.12.5 | Request/response schemas, JSONB content validation | Already used for all schemas |
| httpx | 0.28.1 | Logo.dev API fetching (logo proxy endpoint) | Already installed as project dependency |
| Supabase Python SDK | 2.11+ | DB operations via service-role client | Already the DB access layer |
| SvelteKit | 2.50+ | Frontend framework | Already the frontend framework |
| Svelte 5 | 5.51+ | Component model with runes | Already in use |

### Supporting (already installed -- no new dependencies)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-svelte | 0.575 | `Network` icon for sidebar + empty state | Nav item, DiagramCard icons |
| svelte-sonner | 1.0.7 | Toast notifications | Create/delete success/error feedback |
| shadcn-svelte | 1.1 | UI components (Button, Card, Dialog, AlertDialog, Input, Label, Select, Skeleton) | All UI surfaces |

### Alternatives Considered

None. Phase 1 uses exclusively existing stack components. No new npm or pip packages needed.

**Installation:** No installation required. All dependencies already present.

## Architecture Patterns

### Recommended Project Structure (new files only)

```
backend/
  migrations/
    014_diagrams.sql                    # Diagrams table
    015_component_library.sql           # Component library table + seed data
  app/
    api/
      diagrams.py                       # CRUD route handlers
      component_library.py              # List/get endpoints
      logos.py                          # Logo proxy endpoint
    schemas/
      diagrams.py                       # DiagramCreate, DiagramUpdate, DiagramResponse, DiagramContent
      component_library.py              # ComponentLibraryResponse
    services/
      diagram_service.py                # CRUD business logic
      component_library_service.py      # Query logic
  scripts/
    seed_logos.py                        # One-time script: fetch Logo.dev logos, update component_library rows

frontend/
  src/lib/
    components/diagram/
      DiagramCard.svelte                # Card in list view
      CreateDiagramDialog.svelte        # Create dialog
      DeleteDiagramDialog.svelte        # Delete confirmation
      index.ts                          # Barrel export
    services/
      diagrams.ts                       # createDiagramService() factory
    stores/
      diagrams.svelte.ts                # DiagramStore class singleton
    types/
      diagram.ts                        # Diagram, DiagramCreate types
  src/routes/(app)/
    diagrams/
      +page.ts                          # Page loader (fetch diagrams + projects)
      +page.svelte                      # Diagram list page
```

### Pattern 1: SQL Migration (clone from 005_projects.sql)

**What:** PostgreSQL table with UUID PK, user_id FK, RLS, and updated_at trigger
**When to use:** Every new table in this project

```sql
-- 014_diagrams.sql
CREATE TABLE IF NOT EXISTS diagrams (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  project_id       UUID REFERENCES projects(id) ON DELETE SET NULL,
  customer_name    TEXT NOT NULL,
  title            TEXT NOT NULL DEFAULT '',
  content          JSONB NOT NULL DEFAULT '{"systems":[],"connections":[],"settings":{}}',
  schema_version   INTEGER NOT NULL DEFAULT 1,
  thumbnail_base64 TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_diagrams_user_id ON diagrams(user_id);

DROP TRIGGER IF EXISTS trg_diagrams_updated_at ON diagrams;
CREATE TRIGGER trg_diagrams_updated_at
  BEFORE UPDATE ON diagrams
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE diagrams ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS diagrams_all_own ON diagrams;
CREATE POLICY diagrams_all_own ON diagrams
  FOR ALL USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());
```

### Pattern 2: Service Layer (clone from project_service.py)

**What:** Synchronous functions taking `(supabase: Client, user_id: UUID, ...)`, raising `HTTPException` on ownership violations
**When to use:** All CRUD services

```python
# Source: backend/app/services/project_service.py (existing pattern)
def create_diagram(supabase: Client, user_id: UUID, data: DiagramCreate) -> dict:
    row = {
        "user_id": str(user_id),
        **data.model_dump(exclude_unset=True),
    }
    # Convert content Pydantic model to dict for JSONB
    if "content" in row and row["content"] is not None:
        row["content"] = row["content"] if isinstance(row["content"], dict) else row["content"].model_dump()
    if "project_id" in row and row["project_id"] is not None:
        row["project_id"] = str(row["project_id"])
    result = supabase.table("diagrams").insert(row).execute()
    return result.data[0]
```

### Pattern 3: Thin API Route Handler (clone from projects.py)

**What:** `async def` handlers with `Depends(get_current_user)` + `Depends(get_supabase)`, delegating to service layer
**When to use:** All API routes

```python
# Source: backend/app/api/projects.py (existing pattern)
router = APIRouter(prefix="/api/diagrams", tags=["diagrams"])

@router.post("", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    data: DiagramCreate,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    return svc.create_diagram(supabase, user_id, data)
```

### Pattern 4: Frontend Service Factory (clone from projects.ts)

**What:** `createDiagramService(client: ApiClient)` returning typed interface
**When to use:** All frontend API wrappers

```typescript
// Source: frontend/src/lib/services/projects.ts (existing pattern)
export function createDiagramService(client: ApiClient): DiagramService {
    return {
        list: () => client.get<Diagram[]>('/api/diagrams'),
        create: (data) => client.post<Diagram>('/api/diagrams', data),
        delete: (id) => client.delete(`/api/diagrams/${id}`),
    };
}
```

### Pattern 5: Svelte 5 Runes Store (clone from project.svelte.ts)

**What:** Class-based singleton with `$state` fields, `$derived` computeds, and async methods taking a service
**When to use:** All frontend state management

### Pattern 6: SvelteKit Page Load (clone from dashboard/+page.ts)

**What:** `PageLoad` function using `parent()` for auth session, creating API client, fetching data
**When to use:** All authenticated page routes

### Anti-Patterns to Avoid
- **Do NOT use `writable()` or `readable()`**: Legacy Svelte 4 store API. Use `$state` and `$derived` runes.
- **Do NOT use relative imports in backend**: Always `from app.services import diagram_service`.
- **Do NOT skip RLS policies**: Every table must have `ENABLE ROW LEVEL SECURITY` + ownership policy.
- **Do NOT use `getSession()` alone on the server**: Always use `safeGetSession()`.
- **Do NOT use Tailwind config file**: Tailwind v4 uses `@theme` CSS blocks.
- **Do NOT put business logic in route handlers**: Handlers are thin; service layer owns logic.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Company logos | Custom scraper or icon pack | Logo.dev API (`https://img.logo.dev/{domain}?token=KEY&size=128&format=png`) | Millions of logos, simple REST, free 500K/month |
| UUID generation | Application-level UUIDs | `gen_random_uuid()` in Postgres via pgcrypto | Already enabled in migration 001; consistent, collision-free |
| Updated-at trigger | Application-level timestamp | `set_updated_at()` trigger function | Already defined in migration 002; handles all tables uniformly |
| Row-level security | Application-level auth checks | Supabase RLS policies | Defense-in-depth; backend uses service-role (bypasses RLS) but RLS protects direct DB access |
| Monogram generation | Custom SVG rendering | Simple string initials + deterministic color | Trivial computation; no library needed; store as text, render in Phase 2 frontend |
| JSON validation | Manual field checking | Pydantic v2 nested models | Native `model_dump()` / `model_validate()` for JSONB serialization |

**Key insight:** This phase is almost entirely pattern replication. The only genuinely new code is the Logo.dev proxy endpoint and the seed data script.

## m3ter Native Connectors (Verified)

From the official m3ter docs (https://docs.m3ter.com/guides/integrations):

| System | Category | Native Connector |
|--------|----------|:---:|
| Stripe | Billing/Payments | Yes |
| Chargebee | Billing/Payments | Yes |
| Paddle | Billing/Payments | Yes |
| NetSuite | Finance/ERP | Yes |
| QuickBooks | Finance/ERP | Yes |
| Xero | Finance/ERP | Yes |
| Salesforce | CRM | Yes |
| HubSpot | CRM | Yes |
| AWS Marketplace | Cloud Marketplace | Yes |
| Azure Marketplace | Cloud Marketplace | Yes |

**Confidence:** HIGH -- sourced directly from m3ter official documentation.

## Recommended Component Library Seed List (~28 systems)

Based on the locked decision D-01 and discretion for exact list. Organized by functional categories per D-02.

| Category | Systems | Native? |
|----------|---------|:-------:|
| **CRM** | Salesforce, HubSpot | Yes |
| **Billing/Payments** | Stripe, Chargebee, Paddle, Zuora, Recurly | First 3 Yes |
| **Finance/ERP** | NetSuite, QuickBooks, Xero, SAP | First 3 Yes |
| **Cloud Marketplace** | AWS Marketplace, Azure Marketplace | Yes |
| **Analytics** | Snowflake, BigQuery, Redshift, Looker | No |
| **Data Infrastructure** | Segment, Fivetran | No |
| **Cloud Providers** | AWS, Azure, GCP | No |
| **Monitoring** | Datadog, Grafana | No |
| **Messaging** | Slack, Twilio, SendGrid | No |
| **Developer Tools** | GitHub, Jira | No |
| **m3ter** | m3ter (special -- always present) | N/A |

Total: ~28 systems across 10 categories. The `m3ter` entry itself serves as the hub node reference.

**Logo.dev domains for seed script:**

| System | Domain |
|--------|--------|
| Salesforce | salesforce.com |
| HubSpot | hubspot.com |
| Stripe | stripe.com |
| Chargebee | chargebee.com |
| Paddle | paddle.com |
| Zuora | zuora.com |
| Recurly | recurly.com |
| NetSuite | netsuite.com |
| QuickBooks | quickbooks.intuit.com |
| Xero | xero.com |
| SAP | sap.com |
| AWS Marketplace | aws.amazon.com |
| Azure Marketplace | azure.microsoft.com |
| Snowflake | snowflake.com |
| BigQuery | cloud.google.com |
| Redshift | aws.amazon.com |
| Looker | looker.com |
| Segment | segment.com |
| Fivetran | fivetran.com |
| AWS | aws.amazon.com |
| Azure | azure.microsoft.com |
| GCP | cloud.google.com |
| Datadog | datadoghq.com |
| Grafana | grafana.com |
| Slack | slack.com |
| Twilio | twilio.com |
| SendGrid | sendgrid.com |
| GitHub | github.com |
| Jira | atlassian.com |
| m3ter | m3ter.com |

**Note:** Some systems share domains (AWS / AWS Marketplace both use aws.amazon.com, BigQuery / GCP both use cloud.google.com). The seed script should handle deduplication or use specific subdomains. Logo.dev fetches by domain, so AWS and AWS Marketplace would get the same logo -- which is correct behavior.

## Logo.dev API Details

**Confidence:** HIGH -- verified from official docs and pricing page.

| Property | Value |
|----------|-------|
| Endpoint | `https://img.logo.dev/{domain}?token={PUBLISHABLE_KEY}` |
| Authentication | Publishable token as `token` query parameter |
| Free tier | 500,000 requests/month (Community plan) |
| Parameters | `format` (png, webp, jpg), `size` (px), `retina` (true/false) |
| Response | Image binary (the format requested) |
| Fallback | Returns 404 or placeholder for unknown domains |

**Logo proxy endpoint design:**

```python
# backend/app/api/logos.py
import base64
import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/logos", tags=["logos"])

@router.get("/proxy")
async def proxy_logo(
    domain: str = Query(..., min_length=3),
) -> dict:
    """Fetch logo from Logo.dev and return as base64."""
    token = settings.logo_dev_token  # Add to config.py
    url = f"https://img.logo.dev/{domain}?token={token}&size=128&format=png"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, follow_redirects=True, timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Logo not found")
    b64 = base64.b64encode(resp.content).decode()
    return {"logo_base64": f"data:image/png;base64,{b64}", "domain": domain}
```

**Seed script design:** The seed script (`scripts/seed_logos.py`) runs after the migration. It reads all rows from `component_library` where `logo_base64 IS NULL`, fetches from Logo.dev, updates the row. Failures get the monogram fallback (stored as a simple text marker like `monogram:SN` for Snowflake).

## DiagramContent Pydantic Model Design

**Confidence:** MEDIUM -- discretion area; designed for Phase 2 renderer needs.

The `content` JSONB field holds the full diagram state. Phase 1 defines the schema; Phase 2 consumes it for rendering.

```python
from pydantic import BaseModel, Field


class DiagramSystem(BaseModel):
    """A system node placed on the diagram."""
    id: str  # Client-generated UUID
    component_library_id: str | None = None  # FK to component_library (null for custom)
    name: str
    logo_base64: str | None = None  # Cached at placement time
    x: float = 0.0
    y: float = 0.0
    category: str | None = None


class DiagramConnection(BaseModel):
    """A connection between two systems."""
    id: str  # Client-generated UUID
    source_id: str  # DiagramSystem.id
    target_id: str  # DiagramSystem.id
    label: str = ""
    direction: str = "unidirectional"  # unidirectional | bidirectional
    connection_type: str = "api"  # native_connector | webhook_api | custom_build


class DiagramSettings(BaseModel):
    """Global diagram settings."""
    background_color: str = "#1a1f36"  # m3ter navy
    show_labels: bool = True


class DiagramContent(BaseModel):
    """Root content model stored as JSONB."""
    systems: list[DiagramSystem] = Field(default_factory=list)
    connections: list[DiagramConnection] = Field(default_factory=list)
    settings: DiagramSettings = Field(default_factory=DiagramSettings)
```

**Key considerations:**
- `DiagramSystem.id` is a client-generated string UUID (not a DB UUID) since systems exist only within the JSONB content
- `logo_base64` is cached at placement time -- the diagram is self-contained for rendering/export
- Phase 2 will consume `x`, `y` for layout; Phase 1 just stores defaults
- `connection_type` maps to CONN-04's color coding in Phase 2

## Monogram Fallback Strategy

**Recommendation:** Hash-based deterministic color assignment.

```python
def generate_monogram_color(name: str) -> str:
    """Deterministic pastel color from name hash."""
    COLORS = [
        "#4A90D9", "#50C878", "#E67E22", "#9B59B6",
        "#E74C3C", "#1ABC9C", "#F39C12", "#3498DB",
    ]
    return COLORS[hash(name) % len(COLORS)]
```

This ensures the same system always gets the same color, without needing a category-color mapping table. The monogram itself is the first letters of each word (e.g., "Snowflake" -> "SN", "AWS S3" -> "AS").

## Common Pitfalls

### Pitfall 1: JSONB Default Value Syntax
**What goes wrong:** Using a Python dict as the SQL default for JSONB fails. The default must be a JSON string literal.
**Why it happens:** PostgreSQL JSONB columns require string-cast JSON as defaults.
**How to avoid:** Use `DEFAULT '{"systems":[],"connections":[],"settings":{}}'::jsonb` in the migration.
**Warning signs:** Migration fails with syntax error.

### Pitfall 2: Supabase Service-Role vs RLS
**What goes wrong:** Service-role client bypasses RLS, so ownership checks must be in the service layer. Forgetting ownership checks means any authenticated user can access any diagram.
**Why it happens:** The backend uses service-role key (full access) for flexibility.
**How to avoid:** Always `.eq("user_id", str(user_id))` in every query, matching the `project_service.py` pattern.
**Warning signs:** No `user_id` filter in a Supabase query.

### Pitfall 3: Logo.dev Token in Frontend
**What goes wrong:** Exposing the Logo.dev publishable token in frontend code. While it's a "publishable" key, the proxy endpoint keeps all external API calls server-side.
**Why it happens:** Temptation to call Logo.dev directly from the browser.
**How to avoid:** Logo.dev calls only happen in (a) the seed script and (b) the `/api/logos/proxy` endpoint. Frontend never calls Logo.dev directly.
**Warning signs:** `img.logo.dev` URL appearing in frontend code.

### Pitfall 4: Pydantic model_dump for JSONB Insert
**What goes wrong:** Passing a Pydantic model object directly to `supabase.table().insert()` fails because the Supabase SDK expects plain dicts.
**Why it happens:** `data.model_dump()` returns nested Pydantic models as dicts, but if `content` is a `DiagramContent` instance, it must be explicitly dumped.
**How to avoid:** Always call `.model_dump(mode="json")` on the content field before inserting.
**Warning signs:** `TypeError: Object of type DiagramContent is not JSON serializable`.

### Pitfall 5: UUID Stringification
**What goes wrong:** Passing UUID objects to Supabase client instead of strings.
**Why it happens:** Pydantic models may contain UUID fields.
**How to avoid:** Convert all UUID fields to `str()` before Supabase operations, matching the existing pattern in `project_service.py`.
**Warning signs:** `TypeError` or serialization errors on insert.

### Pitfall 6: Frontend TestClient and Lifespan
**What goes wrong:** Using `with TestClient(app)` triggers the FastAPI lifespan which tries to connect to Postgres.
**Why it happens:** Lifespan opens DB pool and checkpointer pool.
**How to avoid:** Use `TestClient(app, raise_server_exceptions=False)` WITHOUT `with` context manager, matching the existing `authed_client` fixture pattern.
**Warning signs:** Connection refused errors in unit tests.

### Pitfall 7: Logo.dev API Key as Environment Variable
**What goes wrong:** Forgetting to add `LOGO_DEV_TOKEN` to the backend config, causing the proxy endpoint and seed script to fail.
**Why it happens:** New external service dependency.
**How to avoid:** Add `logo_dev_token: str = ""` to `app/config.py` Settings class. Document in `.env.example`.
**Warning signs:** Empty token in Logo.dev requests returning 401.

## Code Examples

### Migration Pattern (verified from 005_projects.sql)

```sql
-- 015_component_library.sql
CREATE TABLE IF NOT EXISTS component_library (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                 TEXT NOT NULL,
  domain               TEXT NOT NULL DEFAULT '',
  category             TEXT NOT NULL DEFAULT '',
  logo_base64          TEXT,
  is_native_connector  BOOLEAN NOT NULL DEFAULT false,
  display_order        INTEGER NOT NULL DEFAULT 0,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Component library is read-only for all authenticated users (no user_id, no RLS ownership)
-- Service-role handles inserts via migrations/seed script
```

### Pydantic Schema Pattern (verified from schemas/projects.py)

```python
from pydantic import BaseModel, Field

class DiagramCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    title: str = ""
    project_id: UUID | None = None
    content: DiagramContent = Field(default_factory=DiagramContent)
    schema_version: int = 1

class DiagramResponse(BaseModel):
    id: UUID
    user_id: UUID
    customer_name: str
    title: str
    project_id: UUID | None = None
    content: DiagramContent
    schema_version: int
    thumbnail_base64: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

### Frontend Type Pattern (verified from types/api.ts)

```typescript
export interface Diagram {
    id: string;
    user_id: string;
    customer_name: string;
    title: string;
    project_id: string | null;
    content: DiagramContent;
    schema_version: number;
    thumbnail_base64: string | null;
    created_at: string;
    updated_at: string;
}

export interface DiagramCreate {
    customer_name: string;
    title?: string;
    project_id?: string | null;
}

export interface DiagramContent {
    systems: DiagramSystem[];
    connections: DiagramConnection[];
    settings: DiagramSettings;
}
```

### Sidebar Nav Item Addition (verified from AppSidebar.svelte)

```svelte
import { LayoutDashboard, FolderKanban, Building2, Network } from 'lucide-svelte';

const navItems = [
    { title: 'Dashboard', url: '/dashboard', icon: LayoutDashboard },
    { title: 'Projects', url: '/projects', icon: FolderKanban },
    { title: 'Diagrams', url: '/diagrams', icon: Network },
    { title: 'Org Connections', url: '/orgs', icon: Building2 },
];
```

### Backend Test Pattern (verified from test_api_projects.py)

```python
def _diagram_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "user_id": str(MOCK_USER_ID),
        "customer_name": "Acme Corp",
        "title": "",
        "project_id": None,
        "content": {"systems": [], "connections": [], "settings": {}},
        "schema_version": 1,
        "thumbnail_base64": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults

class TestCreateDiagram:
    def test_create_success(self, authed_client, mock_supabase):
        row = _diagram_row(customer_name="Test Corp")
        mock_supabase._table_data["diagrams"] = [row]
        resp = authed_client.post("/api/diagrams", json={"customer_name": "Test Corp"})
        assert resp.status_code == 201
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Clearbit Logo API | Logo.dev (successor) | 2024 | Clearbit deprecated; Logo.dev is the direct replacement with same endpoint style |
| Pydantic v1 `dict()` | Pydantic v2 `model_dump()` | 2023 | Project already on v2; use `model_dump(mode="json")` for JSON-safe output |
| Svelte 4 `writable()` | Svelte 5 `$state` runes | 2024 | Project already on Svelte 5; never use legacy store API |
| `tailwind.config.js` | Tailwind v4 `@theme` CSS blocks | 2025 | Project already on v4; no config file |

**Deprecated/outdated:**
- Clearbit Logo API: Deprecated, migrated to Logo.dev
- Pydantic v1 `.dict()` method: Use `.model_dump()` in v2

## Open Questions

1. **Logo.dev token acquisition**
   - What we know: Free tier requires registration at logo.dev, provides a publishable token
   - What's unclear: Whether the user already has a Logo.dev account/token
   - Recommendation: Add `LOGO_DEV_TOKEN` to backend config as optional; seed script and proxy endpoint gracefully degrade to monogram fallback when token is missing

2. **Component library read access control**
   - What we know: The component library is reference data (same for all users), not user-owned
   - What's unclear: Whether RLS should allow all authenticated users to SELECT, or if the table should have no RLS (service-role only)
   - Recommendation: No RLS on component_library table. The GET endpoint uses service-role client (which bypasses RLS anyway). This is read-only reference data. Authentication is still enforced at the API layer via `get_current_user`.

3. **DiagramContent validation depth in Phase 1**
   - What we know: D-11 says backend validates on save; DiagramContent defines the contract
   - What's unclear: How strict validation should be in Phase 1 (Phase 2 will evolve the schema)
   - Recommendation: Validate the top-level shape (systems array, connections array, settings object) but allow flexibility in nested fields. Use `schema_version` to gate stricter validation later.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12+ | Backend API | Yes (3.14.3) | 3.14.3 | -- |
| Node.js 24+ | Frontend | Yes | 24.13.0 | -- |
| Docker | Local Supabase | Yes | 29.2.1 | -- |
| httpx | Logo proxy endpoint | Yes | 0.28.1 | -- |
| PostgreSQL (via Supabase) | Data storage | Yes (via Docker) | 15.8 | -- |
| Logo.dev API | Logo fetching | External | N/A | Monogram fallback (D-08) |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:**
- Logo.dev API token: If not configured, seed script generates monograms; proxy endpoint returns 404 (frontend falls back to monogram). Fully functional without it.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework (backend) | pytest 8.0+ with pytest-asyncio 0.24+ |
| Config file (backend) | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command (backend) | `cd backend && source .venv/bin/activate && pytest tests/test_api_diagrams.py -x` |
| Full suite command (backend) | `cd backend && source .venv/bin/activate && pytest -m "not integration and not eval_live" -x` |
| Framework (frontend) | Vitest 4.0 (jsdom environment) |
| Config file (frontend) | `frontend/vitest.config.ts` |
| Quick run command (frontend) | `cd frontend && npm run test -- --run src/lib/stores/diagrams.svelte.test.ts` |
| Full suite command (frontend) | `cd frontend && npm run test` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PERS-01 | Create diagram with customer_name via API | unit | `pytest tests/test_api_diagrams.py::TestCreateDiagram -x` | Wave 0 |
| PERS-01 | Get diagram returns all fields including content | unit | `pytest tests/test_api_diagrams.py::TestGetDiagram -x` | Wave 0 |
| PERS-07 | Schema_version field persisted and returned | unit | `pytest tests/test_api_diagrams.py::TestCreateDiagram::test_schema_version -x` | Wave 0 |
| NAV-01 | Sidebar renders Diagrams nav item | unit (frontend) | `vitest run src/lib/components/layout/AppSidebar.svelte.test.ts` | Wave 0 (optional) |
| NAV-02 | Diagram can be linked to project_id | unit | `pytest tests/test_api_diagrams.py::TestCreateDiagram::test_with_project_id -x` | Wave 0 |
| NAV-03 | Create diagram endpoint returns 201 | unit | `pytest tests/test_api_diagrams.py::TestCreateDiagram::test_create_success -x` | Wave 0 |
| NAV-04 | Delete diagram endpoint returns 204 | unit | `pytest tests/test_api_diagrams.py::TestDeleteDiagram -x` | Wave 0 |
| COMP-01 | Component library endpoint returns seeded systems | unit | `pytest tests/test_api_component_library.py::TestListComponents -x` | Wave 0 |
| COMP-03 | Component library returns category field | unit | `pytest tests/test_api_component_library.py::TestListComponents::test_categories -x` | Wave 0 |
| COMP-06 | Logo proxy returns base64 for valid domain | unit | `pytest tests/test_api_logos.py::TestLogoProxy -x` | Wave 0 |
| PERS-01 | DiagramStore create/delete updates list | unit (frontend) | `vitest run src/lib/stores/diagrams.svelte.test.ts` | Wave 0 |

### Sampling Rate
- **Per task commit:** Quick run command for affected test file
- **Per wave merge:** Full backend + frontend suite
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_api_diagrams.py` -- covers PERS-01, PERS-07, NAV-02, NAV-03, NAV-04
- [ ] `backend/tests/test_api_component_library.py` -- covers COMP-01, COMP-03
- [ ] `backend/tests/test_api_logos.py` -- covers COMP-06
- [ ] `frontend/src/lib/stores/diagrams.svelte.test.ts` -- covers PERS-01 (frontend store)

## Sources

### Primary (HIGH confidence)
- Existing codebase: `backend/migrations/005_projects.sql`, `backend/app/api/projects.py`, `backend/app/services/project_service.py`, `backend/app/schemas/projects.py` -- verified migration, API, service, and schema patterns
- Existing codebase: `frontend/src/lib/services/projects.ts`, `frontend/src/lib/stores/project.svelte.ts`, `frontend/src/routes/(app)/dashboard/+page.svelte` -- verified frontend service, store, and page patterns
- Existing codebase: `frontend/src/lib/components/layout/AppSidebar.svelte` -- verified sidebar nav item pattern
- Existing codebase: `backend/tests/conftest.py`, `backend/tests/test_api_projects.py` -- verified test fixture and assertion patterns
- Logo.dev pricing page (https://www.logo.dev/pricing) -- 500K requests/month free tier confirmed
- Logo.dev docs (https://www.logo.dev/docs/) -- API endpoint format: `https://img.logo.dev/{domain}?token=KEY`
- m3ter docs (https://docs.m3ter.com/guides/integrations) -- native connector list: Stripe, Chargebee, Paddle, NetSuite, QuickBooks, Xero, Salesforce, HubSpot, AWS Marketplace, Azure Marketplace

### Secondary (MEDIUM confidence)
- DiagramContent model design -- based on Phase 2 renderer needs (REND-02, REND-04) and existing m3ter diagram visual style; field names are Claude's discretion per CONTEXT.md
- Component library seed list (~28 systems) -- assembled from D-01 explicit list + common SE tooling; exact list is Claude's discretion per CONTEXT.md

### Tertiary (LOW confidence)
- Logo.dev response behavior for unknown domains (404 vs placeholder) -- not verified in official docs; seed script should handle both gracefully

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies; exclusively existing MIRA stack
- Architecture: HIGH -- direct clone of proven codebase patterns (projects module)
- Pitfalls: HIGH -- all pitfalls derived from existing codebase gotchas and verified patterns
- Component library seed data: MEDIUM -- exact system list is discretionary
- DiagramContent model: MEDIUM -- field design is discretionary; will evolve in Phase 2
- Logo.dev API: HIGH -- endpoint format and free tier verified from official sources

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable -- all patterns are from the existing codebase; Logo.dev API is the only external dependency)

## Project Constraints (from CLAUDE.md)

- **Tech stack**: Must use existing MIRA stack (SvelteKit, Tailwind v4, shadcn-svelte, Supabase, FastAPI)
- **Python conventions**: Ruff linting (E, F, I, N, W, UP), line-length 100, `async def` handlers, `from app.*` absolute imports, `str | None` union syntax
- **TypeScript conventions**: Svelte 5 runes only (no legacy stores), `lang="ts"` on all script blocks, `cn()` for class merging
- **Test conventions**: Backend `pytest -m "not integration and not eval_live"` for unit tests; Frontend `vitest` with jsdom; MockPostgrestBuilder pattern for Supabase mocking
- **Backend pattern**: Thin route handlers -> service layer -> Supabase client; `Depends(get_current_user)` + `Depends(get_supabase)` for DI
- **Frontend pattern**: Factory service functions, class-based singleton stores with `$state`/`$derived`, `$lib` path aliases
- **Security**: RLS on all tables, ownership checks in service layer, never expose API keys to frontend
- **GSD workflow**: Use GSD commands for all code changes
