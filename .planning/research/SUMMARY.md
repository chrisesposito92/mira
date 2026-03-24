# Project Research Summary

**Project:** m3ter Integration Architecture Diagram Configurator (MIRA feature add-on)
**Domain:** Branded diagram builder — configurator-style, not WYSIWYG canvas editor
**Researched:** 2026-03-23
**Confidence:** HIGH

## Executive Summary

This feature adds an in-app branded diagram configurator to the existing MIRA monorepo, enabling Solutions Engineers to produce on-brand m3ter integration architecture diagrams in under 10 minutes and export them as high-quality PNG or SVG for proposals and presentations. The product is a configurator, not a freeform canvas editor — users assemble diagrams via a structured form UI, and a live SVG preview renders from the resulting data model. This constraint is the central design decision: it guarantees visual consistency and protects brand fidelity regardless of SE skill level, which is the tool's primary value over generic alternatives like Lucidchart or manual slide work.

The recommended approach is a hand-authored reactive SVG component for the diagram renderer (not a graph library like Svelte Flow), `html-to-image@1.11.11` (pinned) for PNG export, and Logo.dev via a backend proxy for company logo resolution. The existing SvelteKit + FastAPI + Supabase stack requires only one net-new frontend library (`html-to-image`). The data model uses normalized Postgres tables (`diagrams`, `diagram_nodes`, `diagram_edges`, `component_library`) rather than a JSONB blob, enabling atomic node/edge updates and future queryability. A `schema_version` field must be included from day one to allow safe schema evolution without breaking saved diagrams.

The highest-risk area is the export pipeline: cross-origin images (logos fetched from CDNs) taint the HTML Canvas and silently produce blank exports; web fonts must be inlined as base64 before rasterization; Tailwind dynamic classes will be purged from production builds breaking color-coded connection pills; and all exports must render at 2x pixel ratio for Retina presentation quality. Every one of these pitfalls is a "looks done but isn't" trap that only surfaces in production. The mitigation is to establish the backend logo proxy, inline-style approach for data-driven colors, and 2x export path during the rendering phase — not retrofitted later.

---

## Key Findings

### Recommended Stack

The existing monorepo stack (SvelteKit, Tailwind v4, FastAPI, Supabase, TypeScript) is sufficient for this feature. Only one net-new frontend library is required. Svelte Flow (`@xyflow/svelte`) is explicitly deferred to a future phase if interactive drag-and-drop canvas editing is ever scoped — it adds unnecessary drag/pan machinery for a fixed hub-and-spoke topology where positions are computed deterministically from the data model.

**Core technologies:**
- Custom reactive SVG component (no lib): diagram renderer — hand-authored SVG gives exact visual control, zero bundle overhead, and the cleanest export path
- `html-to-image@1.11.11` (pinned): PNG export — the Svelte Flow team's own example pins to this version; 1.11.12+ has a known regression (open issue #516)
- Logo.dev CDN + FastAPI backend proxy: company logo resolution — free tier (500K req/mo), proxied server-side to avoid canvas taint and rate-limit exposure; Clearbit is dead (discontinued December 2025)
- Bundled inline SVGs: logos for the curated ~30 m3ter native connectors — zero latency, zero CORS, works offline, perfect for export
- `@dagrejs/dagre@3.0.0`: auto-layout fallback (deferred, not needed for v1 fixed topology) — use the `@dagrejs` fork, not the abandoned `dagre` package

### Expected Features

The complete feature set is split into P1 (must-have for launch), P2 (should-have), and P3 (future). The core tension is between building every diagramming feature SEs could imagine versus building a tool that does one thing perfectly: produce polished m3ter-branded diagrams faster than manual slide work.

**Must have (table stakes):**
- Add/remove system nodes (form-driven, not drag-and-drop) — the core building block
- Define connections between nodes with type and label (Native Connector / Webhook+API / Custom Build)
- Persistable diagrams with list view, save, open, rename — tied to customer name, optional project link
- PNG export at 2x pixel ratio and SVG export — primary SE output format for slides and proposals
- m3ter hub node: locked, centered, shows internal capability labels, non-removable
- "Your Product/Platform" top node: customizable prospect name
- Pre-seeded component library: ~9 m3ter native connectors (Salesforce, NetSuite, Stripe, etc.) + custom node with name input
- Company logos via Logo.dev proxy with monogram fallback
- Live SVG preview alongside configurator panel
- m3ter branded rendering: navy background, white cards, green accent, dashed connections, colored connection pills
- Grouped system categories: Front Office / Finance / Analytics / Custom
- Undo/redo (20-step minimum)
- Duplicate diagram

**Should have (differentiators, add post-launch):**
- Thumbnail generation for diagram list view (add when list grows beyond ~10 diagrams)
- Diagram search/filter in list view
- Additional system categories driven by SE feedback
- Custom node logo URL override for when API lookup fails
- Diagram linked to a MIRA Project (FK to existing `projects` table)

**Defer (v2+):**
- Vertical templates (AI/ML billing, IoT metering) — wait for real usage patterns
- Shareable read-only link — PNG/SVG export covers current need
- Complexity scoring sidebar, annotations layer — validated only if SEs report they help

**Anti-features to actively refuse:**
- Freeform drag-and-drop canvas positioning — destroys brand consistency, which is the tool's core value
- Real-time multiplayer — CRDT complexity out of proportion to need; SEs are individual contributors
- AI-generated diagrams from text — LLM topologies will hallucinate connections; configurator is already faster
- General shape library — scope creep; makes MIRA a worse Lucidchart

### Architecture Approach

The feature follows a Separated Presentation pattern: `DiagramStore` (Svelte 5 runes `$state` class) owns mutable edit state, and a `$derived` render data object is the only input to `DiagramRenderer` (a pure SVG component that emits no events). This separation is mandatory — the renderer SVG element is also the export source, so it must never contain edit-mode ephemera like selection highlights or hover states. The data model uses normalized Postgres tables (not a JSONB blob), with debounced auto-save (500ms idle) to avoid conflict with undo/redo chains. All logo resolution happens at node-creation time, not render time — resolved URLs are stored in `diagram_nodes.logo_url` and persisted.

**Major components:**
1. `DiagramStore` (`stores/diagram.svelte.ts`) — single source of truth for nodes, edges, edit state, undo stack; follows the same class-based Svelte 5 runes pattern as `ObjectsStore`
2. `DiagramRenderer` (`components/diagram/DiagramRenderer.svelte`) — pure SVG render output consuming only `renderData`; SVG sub-components in `nodes/` subfolder
3. `DiagramBuilder` (`components/diagram/DiagramBuilder.svelte`) — composition root connecting configurator panels to the store and renderer
4. `SystemPicker` / `ConnectionForm` / `NodeConfigPanel` — configurator UI panels, read/write to `DiagramStore`
5. Backend: `api/diagrams.py` (CRUD + export), `api/component_library.py` (seeded system search), `db/diagram_repository.py` (Supabase CRUD)
6. DB: `diagrams`, `diagram_nodes`, `diagram_edges`, `component_library` tables (migration `014_diagrams.sql`)
7. `ExportService` (`services/export.ts`) — client-side `html-to-image` pipeline with pre-export logo inlining and font base64 injection

**Build order determined by dependencies:**
DB schema → Backend CRUD + library seed → `DiagramStore` + types → `DiagramRenderer` (pure SVG, testable with mock data) → configurator panels + `SystemPicker` → diagram list view → export pipeline

### Critical Pitfalls

1. **Cross-origin canvas taint** — logos fetched directly from CDNs (Logo.dev, Brandfetch) taint the HTML Canvas and cause silent export failures (`SecurityError`). Prevention: route all logo fetches through a FastAPI backend proxy (`GET /api/logos/proxy?domain=stripe.com`) that serves images from the same origin; store resolved logos as base64 in `diagram_nodes.logo_url` at node-creation time. This must be built in the logo management phase — retrofitting is high-cost.

2. **Tailwind dynamic classes purged in production** — connection type colors (green/blue/orange) built from dynamic Tailwind class strings (e.g., `bg-${color}-500`) are excluded from the production CSS bundle. Prevention: use hardcoded hex values applied via inline `style` attributes for all data-driven colors; Tailwind classes only for structural/static styles.

3. **Web fonts stripped from SVG export** — `@font-face` and `@import` declarations are not fetched by the browser when rasterizing an SVG as an image. Prevention: bundle the m3ter brand font in static assets, fetch it once, and inject as a base64 `@font-face` block into the export clone before calling `toPng()`.

4. **HiDPI pixelated exports** — exporting at 1x resolution produces blurry images on Retina displays. Prevention: hardcode `pixelRatio: 2` in the export function from day one; offer a 2x/3x option in UI. Never export at `window.devicePixelRatio` (may be 1 in dev/CI).

5. **Diagram JSON schema breaks on field rename** — fields renamed without a migration strategy silently break saved diagrams. Prevention: include `schema_version: 1` in the TypeScript type definition before the first diagram is persisted; write a `migrateSchema()` function that handles version transitions on read (lazy migration). 5 minutes to add; permanent value.

6. **SSR crash on canvas/SVG APIs** — `html-to-image` and direct DOM manipulation are browser-only APIs. Prevention: wrap all canvas/export library imports in `onMount` or dynamic `import()` to prevent server-side execution.

---

## Implications for Roadmap

Based on the dependency chain in ARCHITECTURE.md and the phase warnings in PITFALLS.md, a 4-phase structure is recommended:

### Phase 1: Data Foundation

**Rationale:** All other phases depend on the DB schema and backend API existing. The normalized table structure (`diagrams`, `diagram_nodes`, `diagram_edges`, `component_library`) must be established with `schema_version` on the diagram type before any UI work begins. Seeding the component library here means the frontend can immediately work with real data.

**Delivers:**
- Migration `014_diagrams.sql` with all 4 tables, RLS policies, and indexes
- FastAPI routers: `api/diagrams.py` (full CRUD) and `api/component_library.py` (search + seed)
- `db/diagram_repository.py` following existing repository pattern
- `schemas/diagrams.py` Pydantic models with `schema_version: int = 1`
- Seed data: `data/component_library.json` with ~9 m3ter native connectors + metadata

**Addresses:** Persistable diagrams, diagram list, component library, `schema_version` pitfall

**Avoids:** Schema-breaks-on-rename pitfall (include `schema_version` from the start)

### Phase 2: Rendering Engine and Logo Infrastructure

**Rationale:** The m3ter branded SVG renderer is the critical-path component. Everything downstream — export, configurator, live preview — depends on it working correctly. This is also the phase to establish the logo proxy and inline-style patterns that prevent export failures. Getting these patterns right now avoids painful retrofitting later.

**Delivers:**
- `DiagramStore` class (Svelte 5 runes) with `nodes`, `edges`, `renderData` derived, undo/redo stack
- `DiagramRenderer.svelte` — pure SVG with `SystemNode`, `ConnectionLine`, `M3terHubNode` sub-components
- Backend logo proxy endpoint: `GET /api/logos/proxy?domain={domain}` (httpx fetch + base64 return)
- Logo resolution strategy: bundled SVGs for native connectors, Logo.dev proxy for custom nodes, monogram fallback
- Inline-style convention for all data-driven colors (connection type pill colors hardcoded as hex constants)
- TypeScript types: `DiagramNode`, `DiagramEdge`, `DiagramDoc`, `RenderData`

**Addresses:** m3ter brand fidelity renderer, company logos, connection type color coding, m3ter hub node, "Your Product/Platform" node

**Avoids:** Cross-origin canvas taint (proxy established here), Tailwind class purge (inline-style convention established here)

### Phase 3: Configurator UI and Diagram Builder

**Rationale:** With the renderer and store in place, the configurator panels are straightforward form components. The diagram builder route can be wired up, and the component library endpoint enables the system picker. Auto-save with debouncing is implemented here.

**Delivers:**
- `DiagramBuilder.svelte` — composition root with 2-panel layout (configurator left, renderer right)
- `SystemPicker.svelte` — component library browser with category filter and search
- `ConnectionForm.svelte` — add/edit connections with type selector and label
- `NodeConfigPanel.svelte` — edit selected node name, logo, category
- Routes: `/diagrams` (list view), `/diagrams/new`, `/diagrams/[diagramId]`
- Auto-save: debounced 500ms, does not fire during undo/redo chains
- `DiagramListCard.svelte` — card with customer name, last-edited timestamp, duplicate action

**Addresses:** All P1 table-stakes features: add/remove nodes, connection type selector, grouped categories, live preview, diagram list, edit existing, duplicate

**Avoids:** Edit-mode state leaking into renderer (overlay pattern via `DiagramBuilder`, not `DiagramRenderer`)

### Phase 4: Export Pipeline

**Rationale:** Export is implemented last because it wraps the completed renderer. The client-side `html-to-image` path can be built and tested in isolation once the renderer is stable. This phase includes the font inlining and image pre-fetching steps that make export production-ready.

**Delivers:**
- `ExportService` (`services/export.ts`): `exportDiagramToPng()` and `exportDiagramToSvg()` functions
- Pre-export clone preparation: `inlineExternalImages()` (base64 conversion), `inlineFont()` (base64 m3ter brand font injection)
- `html-to-image@1.11.11` integration with `pixelRatio: 2` hardcoded
- Export button in `DiagramRenderer` / `DiagramBuilder` toolbar with "preparing export..." loading state
- Optional: server-side `POST /api/diagrams/{id}/export/png` via CairoSVG (safety net for headless contexts)
- "Looks done but isn't" export verification checklist (PITFALLS.md) enforced via manual QA

**Addresses:** PNG export (2x), SVG export, HiDPI quality, font rendering in exports, export isolation (no selection state captured)

**Avoids:** Web fonts stripped from export (inline font), HiDPI blur (2x hardcoded), cross-origin taint (pre-fetch step), edit-mode state in export (separate clone)

### Phase Ordering Rationale

- **DB schema must be first** — ARCHITECTURE.md explicitly identifies this as the dependency root. No backend, store, or UI can proceed without it.
- **Renderer before configurator** — the renderer is the critical-path component. `DiagramRenderer` can be developed and tested with mock data independently of the configurator panels, but the panels depend on the store interface that the renderer's architecture defines.
- **Logo proxy in Phase 2, not Phase 4** — a core pitfall finding: establishing the proxy and inline-style patterns during the rendering phase prevents painful retrofits. Logos must be resolved and stored at node-creation time, which is a Phase 2/3 concern, not an export-phase concern.
- **Export last** — it wraps the completed renderer; building it last ensures the source SVG is stable and final.

### Research Flags

Phases that should proceed with standard patterns (skip `research-phase`):
- **Phase 1 (Data Foundation):** Standard Supabase + FastAPI CRUD following existing patterns (`projects`, `use_cases`). No novel patterns.
- **Phase 3 (Configurator UI):** Standard SvelteKit form components + Svelte 5 runes store. Well-documented existing patterns in the codebase.

Phases that may benefit from a targeted spike before full implementation:
- **Phase 2 (Rendering Engine):** The pure SVG component for the m3ter branded layout requires precise layout math (polar/radial positioning for hub-and-spoke). The exact coordinate system, viewBox sizing, and SVG text layout constraints for node cards should be prototyped before the full component is built. Not a research gap — a design/implementation spike.
- **Phase 4 (Export Pipeline):** The `html-to-image` font inlining path (`fetchStyle` option) is documented as unreliable across CORS. Verify the explicit base64 font injection approach works against the specific m3ter brand font before the full export service is written. Low-effort spike, high value.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Primary choices verified via npm (exact versions), official Svelte Flow docs, Logo.dev pricing page, and GitHub issue tracking for html-to-image regression. The "no Svelte Flow in v1" decision is strongly supported by the fixed-topology constraint. |
| Features | HIGH | Feature set derived from m3ter's own integrations documentation and a clear understanding of SE workflow. The anti-features list is particularly well-reasoned — each exclusion maps to a specific way it would undermine the core value proposition. |
| Architecture | HIGH | All patterns are direct extensions of existing MIRA codebase conventions (class-based Svelte 5 runes stores, factory function services, FastAPI repository pattern). Separated Presentation is an established pattern with clear precedent. |
| Pitfalls | HIGH | Cross-origin canvas taint, font export, and Tailwind JIT purge are all documented against real GitHub issues, MDN, and library-specific guides. The schema versioning pitfall is industry-standard; the HiDPI issue is straightforward canvas math. |

**Overall confidence:** HIGH

### Gaps to Address

- **Logo.dev token management:** The backend proxy requires a Logo.dev API token. Confirm whether the free tier (500K req/mo, attribution required) is sufficient for the expected SE usage volume, or if the Startup plan ($280/yr) is needed. Add `LOGO_DEV_API_TOKEN` to `.env` and backend environment docs.

- **m3ter brand font specifics:** The export pipeline requires the m3ter brand font to be bundled in static assets. Confirm the exact font name and file (the MIRA codebase does not currently use a custom m3ter brand font — the diagram renderer may need to use a system font or Inter for v1, which simplifies the export font-inlining step significantly).

- **Component library scope:** The research identifies ~9 native connectors from m3ter's integrations docs (Salesforce, NetSuite, Stripe, QuickBooks, Xero, HubSpot, Chargebee, Paddle, Webhooks). The AGENTS.md mentions "~30 m3ter native connectors" as the bundled SVG logo scope. Reconcile the exact seed list before starting Phase 1 to avoid mid-phase additions.

- **Thumbnail generation timing:** ARCHITECTURE.md calls thumbnails a P2 feature triggered by list growth. PITFALLS.md warns against generating thumbnails synchronously on save. The implementation pattern (async after-save, store in Supabase Storage) is clear, but confirm whether the existing Supabase Storage setup in the project has the necessary bucket configuration.

---

## Sources

### Primary (HIGH confidence)
- https://svelteflow.dev/ — Svelte Flow v1.5.1 confirmed, Svelte 5 runes support, html-to-image@1.11.11 pin
- https://github.com/bubkoo/html-to-image — library source, issue #516 regression, toPng() API
- https://www.logo.dev/pricing — free tier limits (500K req/mo), migration from Clearbit
- https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/CORS_enabled_image — cross-origin canvas taint specification
- https://docs.m3ter.com/guides/integrations — native connector list used for component library seed

### Secondary (MEDIUM confidence)
- https://www.logo.dev/docs/platform/rate-limits — Logo.dev rate limit specifics
- https://docs.brandfetch.com/logo-api/rate-limits — Brandfetch rate limit specifics (fallback option)
- https://icepanel.io/blog/2025-09-03-top-8-diagramming-tools-for-software-architecture — configurator vs freeform tradeoff analysis
- https://cairosvg.org/ — server-side SVG→PNG fallback (Python, Phase 4 optional)
- npm show results for @xyflow/svelte@1.5.1, html-to-image@1.11.13, @dagrejs/dagre@3.0.0 — verified 2026-03-23

### Tertiary (LOW confidence)
- https://developer.hubspot.com/changelog/upcoming-sunset-of-clearbits-free-logo-api — Clearbit shutdown Dec 2025 (treat as confirmed; do not use Clearbit)
- HiDPI export blur pattern — MDN `devicePixelRatio` docs + industry convention; no single authoritative source beyond the MDN math

---
*Research completed: 2026-03-23*
*Ready for roadmap: yes*
