# Architecture Research

**Domain:** Configurator-style diagram builder embedded in SvelteKit + FastAPI monorepo
**Researched:** 2026-03-23
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (SvelteKit)                          │
├──────────────────────────┬──────────────────────────────────────────┤
│  Configurator UI Layer   │         Preview / Render Layer           │
│  ┌────────────────────┐  │  ┌───────────────────────────────────┐   │
│  │  DiagramStore      │  │  │  DiagramRenderer (SVG component)  │   │
│  │  (edit state)      │──┼─▶│  Reads derived render data only   │   │
│  └────────────────────┘  │  └───────────────┬───────────────────┘   │
│  ┌────────────────────┐  │                  │                        │
│  │  SystemPicker      │  │  ┌───────────────▼───────────────────┐   │
│  │  ConnectionForm    │  │  │  ExportButton                     │   │
│  │  NodeConfigPanel   │  │  │  (triggers export flow)           │   │
│  └────────────────────┘  │  └───────────────────────────────────┘   │
├──────────────────────────┴──────────────────────────────────────────┤
│                         Services Layer                               │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────────┐   │
│  │ DiagramSvc   │  │ LogoService   │  │ ExportService          │   │
│  │ (CRUD REST)  │  │ (logo.dev CDN)│  │ (client SVG→PNG)       │   │
│  └──────────────┘  └───────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                               │  REST
┌──────────────────────────────▼──────────────────────────────────────┐
│                        BACKEND (FastAPI)                             │
│  ┌──────────────────────┐   ┌────────────────────────────────────┐  │
│  │ diagrams.py router   │   │ component_library.py router        │  │
│  │ CRUD + SVG export    │   │ Seeded system nodes + search       │  │
│  └──────────────────────┘   └────────────────────────────────────┘  │
│  ┌──────────────────────┐   ┌────────────────────────────────────┐  │
│  │ DiagramRepository    │   │ SVG export endpoint (CairoSVG)     │  │
│  │ (Supabase CRUD)      │   │ POST /diagrams/{id}/export/png     │  │
│  └──────────────────────┘   └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                        SUPABASE (Postgres)                           │
│  ┌──────────────────┐  ┌────────────────────┐  ┌────────────────┐  │
│  │ diagrams         │  │ diagram_nodes       │  │ diagram_edges  │  │
│  │ (header + meta)  │  │ (systems selected)  │  │ (connections)  │  │
│  └──────────────────┘  └────────────────────┘  └────────────────┘  │
│  ┌──────────────────┐                                               │
│  │ component_library│                                               │
│  │ (seeded systems) │                                               │
│  └──────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `DiagramStore` | Single source of truth for edit state — nodes, edges, layout positions, UI mode | Svelte 5 `$state` class singleton |
| `DiagramRenderer` | Pure render output — consumes derived render data, emits no events, drives the SVG preview | Svelte component, SVG-first |
| `SystemPicker` | Component library browser — search, filter by category, add node to diagram | Svelte component reading library data |
| `ConnectionForm` | Add/edit a connection between two nodes — type, label, direction | Svelte form component |
| `NodeConfigPanel` | Edit a selected node — name, logo, custom fields | Svelte panel |
| `DiagramService` | CRUD REST calls to backend — create, read, update, list, delete | Factory function (`createDiagramService`) |
| `LogoService` | Resolve logos by domain via logo.dev CDN | Thin wrapper, returns URL string |
| `ExportService` | Serialize the live SVG DOM to PNG client-side | `html-to-image` or Canvas blob pipeline |
| `diagrams.py` router | FastAPI endpoints for diagram CRUD and server-side PNG export | Async FastAPI router |
| `component_library.py` router | Serve seeded system nodes, search endpoint | Read-only FastAPI router |
| `DiagramRepository` | Supabase CRUD with RLS, query diagrams by user | Python repository class |

## Recommended Project Structure

```
frontend/src/
├── lib/
│   ├── components/
│   │   └── diagram/               # All diagram feature components
│   │       ├── DiagramBuilder.svelte      # Top-level composition root
│   │       ├── DiagramRenderer.svelte     # Pure SVG render output
│   │       ├── SystemPicker.svelte        # Component library panel
│   │       ├── ConnectionForm.svelte      # Add/edit connection
│   │       ├── NodeConfigPanel.svelte     # Edit selected node
│   │       ├── DiagramListCard.svelte     # Card in list view
│   │       └── nodes/
│   │           ├── SystemNode.svelte      # Individual system card in SVG
│   │           ├── ConnectionLine.svelte  # SVG path for a connection
│   │           └── M3terHubNode.svelte    # Fixed center hub node
│   ├── stores/
│   │   └── diagram.svelte.ts      # DiagramStore (edit state, Svelte 5 runes)
│   ├── services/
│   │   ├── diagram.ts             # REST calls (createDiagramService factory)
│   │   └── logo.ts                # Logo URL resolver (logo.dev)
│   └── types/
│       └── diagram.ts             # DiagramNode, DiagramEdge, DiagramDoc types
└── routes/(app)/
    └── diagrams/
        ├── +page.svelte           # Diagram list view
        ├── +page.server.ts        # SSR list load
        ├── new/
        │   └── +page.svelte       # Create diagram (redirects to [id])
        └── [diagramId]/
            ├── +page.svelte       # Builder + preview
            └── +page.server.ts    # Load diagram by ID

backend/app/
├── api/
│   ├── diagrams.py               # CRUD + export endpoints
│   └── component_library.py     # Seeded library, search
├── db/
│   └── diagram_repository.py    # Supabase CRUD for diagrams
├── schemas/
│   └── diagrams.py              # Pydantic v2 request/response models
└── data/
    └── component_library.json   # Seed data: systems + metadata

backend/migrations/
└── 014_diagrams.sql              # New tables (diagrams, diagram_nodes, diagram_edges, component_library)
```

### Structure Rationale

- **`diagram/` component folder:** Isolated by feature, mirrors the existing pattern (`chat/`, `control-panel/`, `project/`). All SVG sub-components live in `nodes/` so they can be treated as a mini SVG component library.
- **`diagram.svelte.ts` store:** Follows the existing class-based Svelte 5 runes pattern used by `ObjectsStore`, `ProjectStore`, etc. Edit state is separate from the render-only `DiagramRenderer` component.
- **`diagram_repository.py`:** Matches the existing repository pattern (`db/` layer). Owns all Supabase queries so the router stays thin.
- **`data/component_library.json`:** Seed data as a static JSON file keeps library management simple in v1. Background migration seeds the DB table on deploy.

## Architectural Patterns

### Pattern 1: Edit State / Render Data Separation

**What:** The `DiagramStore` owns mutable editing state (selected node, form visibility, drag mode). A separate `$derived` or computed property produces a clean, immutable `RenderData` object that `DiagramRenderer` consumes. The renderer is a pure function of `RenderData` — it has no internal state and emits no DOM events.

**When to use:** Any diagram/canvas feature where the preview must be stable and exportable independently of edit-mode ephemera (selection highlights, hover states, form panels open/closed).

**Trade-offs:** Adds a small data transformation step. The payoff is that the `DiagramRenderer` SVG can be serialized for export without stripping ephemeral UI state — it never had any.

**Example:**
```typescript
// diagram.svelte.ts
class DiagramStore {
  // Mutable edit state
  nodes = $state<DiagramNode[]>([]);
  edges = $state<DiagramEdge[]>([]);
  selectedNodeId = $state<string | null>(null);

  // Pure render data — no edit-mode state
  renderData = $derived<RenderData>({
    nodes: this.nodes,
    edges: this.edges,
    // layout is part of nodes (position stored on node)
  });
}
```

```svelte
<!-- DiagramRenderer.svelte — reads only renderData, never DiagramStore directly -->
<script lang="ts">
  let { renderData }: { renderData: RenderData } = $props();
</script>
<svg id="diagram-render-target" ...>
  {#each renderData.nodes as node}
    <SystemNode {node} />
  {/each}
  {#each renderData.edges as edge}
    <ConnectionLine {edge} />
  {/each}
</svg>
```

### Pattern 2: Normalized Postgres Schema (not JSONB blob)

**What:** Store nodes and edges in their own Postgres tables with typed columns, not as a single JSONB blob on the `diagrams` row. Layout positions (x, y) live on the `diagram_nodes` table as float columns.

**When to use:** When individual nodes and edges need to be queryable, updatable atomically, or join against the component library. The configurator approach (not WYSIWYG canvas) means nodes are added/removed individually — normalized rows map directly to that granularity.

**Trade-offs:** Requires a join query to load a full diagram. Simpler updates (update one node's label without re-serializing the whole diagram). Better for future per-node analytics or diff tracking.

**Schema:**
```sql
-- diagrams: header + customer metadata
CREATE TABLE diagrams (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  project_id   UUID REFERENCES projects(id) ON DELETE SET NULL,
  title        TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- diagram_nodes: one row per system added to a diagram
CREATE TABLE diagram_nodes (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  diagram_id        UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
  library_system_id UUID REFERENCES component_library(id),  -- null for custom nodes
  label             TEXT NOT NULL,
  logo_url          TEXT,
  category          TEXT NOT NULL,   -- 'crm', 'erp', 'payments', 'm3ter', 'custom'
  is_hub            BOOLEAN NOT NULL DEFAULT false,  -- true for m3ter center node
  pos_x             FLOAT NOT NULL DEFAULT 0,
  pos_y             FLOAT NOT NULL DEFAULT 0,
  custom_data       JSONB  -- overflow for node-type-specific fields
);

-- diagram_edges: one row per connection
CREATE TABLE diagram_edges (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  diagram_id    UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
  source_node_id UUID NOT NULL REFERENCES diagram_nodes(id) ON DELETE CASCADE,
  target_node_id UUID NOT NULL REFERENCES diagram_nodes(id) ON DELETE CASCADE,
  label         TEXT NOT NULL DEFAULT '',
  direction     TEXT NOT NULL DEFAULT 'unidirectional',  -- or 'bidirectional'
  connection_type TEXT NOT NULL DEFAULT 'custom',  -- 'native', 'webhook_api', 'custom'
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- component_library: seeded, read-only reference data
CREATE TABLE component_library (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  slug        TEXT NOT NULL UNIQUE,
  category    TEXT NOT NULL,
  logo_url    TEXT,
  is_native_connector BOOLEAN NOT NULL DEFAULT false,
  native_connector_url TEXT,  -- link to m3ter docs
  description TEXT
);
```

### Pattern 3: Client-Side SVG Export (with Server-Side PNG Fallback)

**What:** The primary export path renders the live `DiagramRenderer` SVG in the browser to a PNG using `html-to-image`. The SVG is self-contained (no foreignObject, no external fonts loaded via @import — inline them). A secondary server-side path via `POST /api/diagrams/{id}/export/png` uses CairoSVG as a Python fallback for high-DPI or headless contexts.

**When to use:** Client-side is the default — it's instant, requires no round-trip, and the SE gets immediate feedback. The server path is a safety net for environments where the Canvas API is unavailable (e.g., automated email generation in future).

**Trade-offs:** Client-side `html-to-image` has limitations with `foreignObject` HTML-in-SVG. This is fine here because `DiagramRenderer` is a pure SVG component (no HTML inside SVG). External image tags (logos) must be loaded as data URLs before serialization — see the logo pre-fetch step.

**Example:**
```typescript
// services/export.ts
export async function exportDiagramToPng(svgElementId: string): Promise<Blob> {
  const svgEl = document.getElementById(svgElementId) as SVGElement;
  // Pre-fetch all <image> hrefs as data URLs so they survive serialization
  await inlineExternalImages(svgEl);
  const { toPng } = await import('html-to-image');
  const dataUrl = await toPng(svgEl, { pixelRatio: 2 });
  return dataUrlToBlob(dataUrl);
}
```

### Pattern 4: Logo Resolution Strategy

**What:** Logos are resolved at node-add time, not at render time. When an SE adds a system from the component library, the `logo_url` is already set from seed data. When they add a custom node (e.g., the customer's product), the frontend calls `logo.dev` with the company domain. The resolved URL is stored on `diagram_nodes.logo_url` and persisted to Supabase.

**When to use:** Always. Do not resolve logos live during render — it adds latency, can fail mid-render, and breaks PNG export (external resources blocked by CORS during canvas serialization).

**Trade-offs:** Logos are fetched and stored once. If a company rebrands, stored logos are stale — acceptable for v1.

**Example:**
```typescript
// services/logo.ts — Logo.dev is domain-based, free tier, CDN-served
export function getLogoUrl(domain: string): string {
  return `https://img.logo.dev/${domain}?token=YOUR_TOKEN&size=64`;
}
// Store this URL on the node at creation time, not during render
```

## Data Flow

### Add System to Diagram Flow

```
SE clicks system in SystemPicker
    ↓
DiagramStore.addNode(libraryItem)
    ↓ (if custom node with domain)
LogoService.getLogoUrl(domain) → logo.dev CDN URL
    ↓
DiagramStore.nodes[] updated (optimistic, local)
    ↓
DiagramService.saveNode(diagramId, node) → POST /api/diagrams/{id}/nodes
    ↓
DiagramRepository.insert_node(node) → Supabase diagram_nodes
    ↓
DiagramRenderer re-renders (reactively via $derived renderData)
```

### Save / Persist Flow

```
SE edits node label or connection
    ↓
DiagramStore mutation ($state update)
    ↓  (debounced 500ms)
DiagramService.updateNode / updateEdge → PATCH /api/diagrams/{id}/nodes/{nodeId}
    ↓
DiagramRepository.update_node() → Supabase UPDATE
```

### Export to PNG Flow

```
SE clicks "Export PNG"
    ↓
ExportService.exportDiagramToPng("diagram-render-target")
    ↓
[inline external <image> srcs as data URLs]
    ↓
html-to-image toPng() → canvas serialization → data URL
    ↓
download(dataUrl, "diagram.png")
```

### Load Diagram Flow

```
+page.server.ts (SSR): load diagram header
    ↓
GET /api/diagrams/{id}
    ↓  (join nodes + edges)
DiagramRepository.get_with_nodes_edges(id)
    ↓
Return DiagramDoc (header + nodes[] + edges[])
    ↓
DiagramStore.hydrate(doc) on mount
    ↓
DiagramRenderer renders immediately
```

### State Management

```
DiagramStore ($state)
    ├── nodes[] ──────────────────▶ DiagramRenderer (reactive)
    ├── edges[] ──────────────────▶ DiagramRenderer (reactive)
    ├── selectedNodeId ───────────▶ NodeConfigPanel (conditional render)
    ├── showConnectionForm ────────▶ ConnectionForm (conditional render)
    └── $derived renderData ───────▶ ExportService (snapshot)
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 diagrams | Single Supabase project, no caching needed, direct queries fine |
| 100-10k diagrams | Add index on `diagrams(user_id, updated_at DESC)` for list view. Thumbnail generation at export time (store in Supabase Storage). |
| 10k+ diagrams | Thumbnail cache via Supabase Storage CDN. Consider materializing diagram count per user for dashboard stats. |

### Scaling Priorities

1. **First bottleneck:** Thumbnail images for list view — solved by storing a small PNG thumbnail in Supabase Storage at export time and referencing the URL.
2. **Second bottleneck:** Logo resolution for custom nodes — solved by the logo.dev CDN being responsible for delivery, not the app server.

## Anti-Patterns

### Anti-Pattern 1: Storing the Entire Diagram as a JSONB Blob

**What people do:** Store `{ nodes: [...], edges: [...] }` as a single JSONB column on the `diagrams` table.

**Why it's wrong:** Every save requires deserializing and re-serializing the whole blob. Individual node updates are not atomic. Cannot query across node properties (e.g., "all diagrams that include Salesforce"). Makes the thumbnail generation approach harder.

**Do this instead:** Normalized tables (`diagram_nodes`, `diagram_edges`) with typed columns. Positions (x, y) are floats on `diagram_nodes`. Only truly unstructured per-node overflows go in a `custom_data JSONB` column.

### Anti-Pattern 2: Rendering Logos via External URLs at Export Time

**What people do:** Leave `<image href="https://img.logo.dev/..." />` in the SVG and try to export to PNG.

**Why it's wrong:** The Canvas API blocks cross-origin resources during `drawImage()`. The PNG will either fail or show broken image placeholders. The `html-to-image` library faces the same restriction.

**Do this instead:** Before serializing for export, walk all `<image>` elements and replace their `href` with a base64 data URL fetched via `fetch(...).then(r => r.blob()).then(blobToDataUrl)`. This pre-fetch step must complete before the canvas serialization begins.

### Anti-Pattern 3: Putting Edit-Mode State in the Renderer

**What people do:** Pass `selectedNodeId` and `hoveredNodeId` into `DiagramRenderer` and use them to conditionally apply highlight styles.

**Why it's wrong:** The renderer SVG element is also the export source. Selection rings, highlight borders, and hover states will appear in the exported PNG. The exported image should show only the clean diagram.

**Do this instead:** Keep `DiagramRenderer` props to `renderData` only. Apply selection/hover state as an overlay layer on top of the renderer in `DiagramBuilder.svelte`, using an absolutely-positioned HTML element or a separate SVG layer that is excluded from the export capture.

### Anti-Pattern 4: Using `foreignObject` Inside the Render SVG

**What people do:** Embed HTML `<div>` elements inside the SVG using `<foreignObject>` to get rich text or flex layout.

**Why it's wrong:** `foreignObject` is not reliably serialized to PNG by `html-to-image` or Canvas. Cross-browser support for `foreignObject` in canvas is poor, and SVG export to file loses the HTML content.

**Do this instead:** Use pure SVG primitives (`<text>`, `<rect>`, `<image>`, `<path>`) for everything inside `DiagramRenderer`. Accept that SVG text layout is more constrained than CSS flexbox — design the node cards to work within SVG constraints.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| logo.dev | Frontend CDN URL construction at node-add time | Free tier; store resolved URL, don't call per-render. Token required. |
| Supabase Storage | Store exported PNG thumbnails for list view | Use `diagrams/{userId}/{diagramId}/thumbnail.png` path convention |
| Supabase RLS | User-scoped: `user_id = auth.uid()` on all diagram tables | Same pattern as existing `projects`, `use_cases` tables |
| CairoSVG (Python) | Server-side export endpoint; pip dependency | Only needed for `/export/png` server route; optional for v1 |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `DiagramStore` ↔ `DiagramRenderer` | `$derived` render data, one-way | Renderer is a pure function of store state |
| `DiagramStore` ↔ `DiagramService` | Direct method calls on store actions | Service calls are async; store updates optimistically |
| `DiagramBuilder` ↔ `ExportService` | One-shot function call passing SVG element ID | Export is fire-once, no reactive binding |
| Frontend ↔ FastAPI `/api/diagrams/*` | Standard REST (matches existing pattern) | New router added to `api_router` in `router.py` |
| `diagrams` ↔ `projects` | Optional FK (`project_id REFERENCES projects(id) ON DELETE SET NULL`) | Diagram can exist without a project; link is advisory |

## Build Order Implications

The following dependency chain determines phase ordering:

1. **DB schema first** (`014_diagrams.sql`) — all other components depend on the tables existing.
2. **Backend CRUD + component library seed** — frontend cannot load or persist without endpoints.
3. **`DiagramStore` + type definitions** — frontend components all depend on the shared types and store interface.
4. **`DiagramRenderer` (pure SVG)** — needs store types but no API. Can be built and tested in isolation with mock data.
5. **`SystemPicker` + configurator panels** — needs component library endpoint + store mutations.
6. **Diagram list view** — needs CRUD endpoints.
7. **Export pipeline** — last, because it wraps the completed renderer. Client-side `html-to-image` path can be built independently of CairoSVG server path.

## Sources

- [html-to-image (1.6M+ weekly downloads, 2025 leading approach)](https://github.com/bubkoo/html-to-image)
- [Logo.dev — free company logo API](https://www.logo.dev/)
- [Brandfetch Logo API overview and free tier](https://docs.brandfetch.com/logo-api/overview)
- [CairoSVG Python library for server-side SVG→PNG](https://cairosvg.org/)
- [Ilograph blog: Why to drop drag-and-drop diagram tools](https://www.ilograph.com/blog/posts/its-time-to-drop-drag-and-drop-diagram-tools)
- [Dynamic OG image with SvelteKit and Satori (resvg-js pattern)](https://dev.to/theether0/dynamic-og-image-with-sveltekit-and-satori-4438)
- [Supabase JSONB docs](https://supabase.com/docs/guides/database/json)
- [Svelte Flow — node-based UI library for Svelte](https://svelteflow.dev/)
- [Martin Fowler: Separated Presentation pattern](https://martinfowler.com/eaaDev/uiArchs.html)

---
*Architecture research for: m3ter Integration Architecture Diagrammer (configurator-style, SvelteKit + FastAPI + Supabase)*
*Researched: 2026-03-23*
