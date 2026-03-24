# Phase 2: Rendering Engine - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

A live, m3ter-branded SVG diagram renders correctly from diagram data with logos and color-coded connections. Includes the SVG rendering component, DiagramStore extension for reactive content, hub-and-spoke auto-layout algorithm, connection line rendering with data flow pills, grouped category cards, and a minimal custom node creation dialog with logo preview.

**Requirements in scope:** REND-01, REND-02, REND-03, REND-04, REND-05, COMP-02, COMP-04, COMP-05, CONN-04

</domain>

<decisions>
## Implementation Decisions

### Layout Algorithm
- **D-01:** Zone-based layout — prospect node ("Your Product/Platform") fixed at top-center, m3ter hub dead center, system categories arranged in clockwise zones (left, bottom-left, bottom, bottom-right, right)
- **D-02:** Fixed canvas with reflow — single canvas size, nodes reposition and resize as system count grows. Export dimensions are predictable.
- **D-03:** Automatic zone assignment by category order — `display_order` from the component library table drives clockwise zone fill. No user-assignable zones in v1.

### Connection Line Rendering
- **D-04:** Straight dashed lines — direct point-to-point SVG paths matching m3ter reference style. No curves or orthogonal routing.
- **D-05:** Midpoint pill labels — data flow pill labels (colored rounded rectangles with text) centered on the connection line.
- **D-06:** Dot at source, arrowhead at target — small filled circle at the origin end, arrowhead at the destination. Bidirectional connections get arrowheads at both ends (no dots).

### Category Group Cards
- **D-07:** Logo grid — systems inside a category group card render as small logo squares in rows (2-3 per row) with names below each logo.
- **D-08:** Text-only header — category name in bold/muted text at the top of the white containing card. No colored bars or icons — keeps the visual hierarchy clean and avoids competing with connection type colors.
- **D-09:** Individual cards for standalone systems — ungrouped systems, custom nodes, and single-system categories render as standalone white rounded cards with logo + name, without a category wrapper.

### Custom Node Creation
- **D-10:** Minimal dialog — simple "Add Custom System" modal with name field + domain field, accessible from a "+" button on the diagram page. Meets COMP-02 without building the full Phase 3 configurator.
- **D-11:** Live preview on domain blur — when the domain field loses focus, the logo proxy is called and a preview shows the fetched logo (or monogram fallback). User sees what they're getting before committing.

### Claude's Discretion
- Exact canvas dimensions and SVG coordinate system
- Font choice — Inter as default (per STATE.md: "if m3ter brand font unavailable, use Inter")
- Spacing constants, card dimensions, border radius, shadow styling
- Dashed line `stroke-dasharray` pattern and stroke width
- Logo grid column count per card width (2 vs 3 per row)
- Monogram SVG rendering (parsing `monogram:<INITIALS>:<COLOR>` format from Phase 1)
- DiagramStore reactive state extension for content editing
- SVG marker definitions for dots and arrowheads
- Exact pill label sizing, padding, font size

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data Model (Phase 1 output)
- `backend/app/schemas/diagrams.py` — DiagramContent, DiagramSystem, DiagramConnection, DiagramSettings Pydantic models. Defines the data contract the renderer consumes.
- `frontend/src/lib/types/diagram.ts` — TypeScript types mirroring backend schemas. DiagramSystem has x/y coords, DiagramConnection has connection_type enum.
- `frontend/src/lib/stores/diagrams.svelte.ts` — Existing DiagramStore (list/create/delete). Phase 2 extends this with content editing state.
- `frontend/src/lib/services/diagrams.ts` — DiagramService factory with CRUD + component library endpoints. Renderer calls `update()` to persist content changes.

### Backend APIs (Phase 1 output)
- `backend/app/api/diagrams.py` — CRUD endpoints including PATCH for content updates
- Component library endpoint (`GET /api/component-library`) — returns seeded systems with `logo_base64`, `category`, `is_native_connector`, `display_order`
- Logo proxy endpoint (`GET /api/logo-proxy?domain=X`) — fetches and returns base64 logo, used by custom node creation

### Existing Frontend Patterns
- `frontend/src/lib/components/ui/` — shadcn-svelte base components (Card, Button, Dialog, Input)
- `frontend/src/routes/(app)/diagrams/` — Existing diagram list page; Phase 2 adds a detail/editor route
- `frontend/src/lib/utils.ts` — `cn()` utility for class merging

### Project Documentation
- `.planning/PROJECT.md` — Core constraints (must use existing MIRA stack), configurator-over-WYSIWYG decision
- `.planning/REQUIREMENTS.md` — Full requirement list with phase mapping; Phase 2 requirements: REND-01 through REND-05, COMP-02, COMP-04, COMP-05, CONN-04
- `.planning/phases/01-data-foundation/01-CONTEXT.md` — Phase 1 decisions including logo approach (D-05 through D-08), monogram format, data model decisions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DiagramStore` class (`stores/diagrams.svelte.ts`) — Svelte 5 runes singleton with list/create/delete. Extend with `currentDiagram`, `updateContent()`, reactive derived state for the renderer.
- `DiagramService` (`services/diagrams.ts`) — Already has `update(id, data)` for PATCH and `listComponents()` for the component library. No new endpoints needed.
- `ApiClient` (`services/api.ts`) — Base HTTP client with auth headers. Logo proxy calls go through this.
- shadcn-svelte `Dialog`, `Input`, `Button` — Reuse for the custom node creation modal.
- `cn()` utility — For conditional class merging on any wrapper elements.

### Established Patterns
- Svelte 5 runes (`$state`, `$derived`, `$effect`) — All reactive state. The SVG renderer should use `$derived` to recompute layout when `content.systems` or `content.connections` change.
- Class-based store singletons — DiagramStore pattern; extend rather than create a separate "renderer store."
- Factory function services (`createDiagramService(client)`) — Consistent with existing codebase.
- Route structure: `(app)/diagrams/` exists; add `[id]/+page.svelte` for the editor/preview route.

### Integration Points
- `frontend/src/routes/(app)/diagrams/+page.svelte` — List page; clicking a diagram navigates to `[id]` editor route
- `frontend/src/routes/(app)/diagrams/[id]/` — New route for diagram editor with live SVG preview
- `backend/app/api/diagrams.py` — PATCH endpoint already exists for saving content updates
- `backend/app/api/diagrams.py` — Logo proxy endpoint already exists for custom node logo fetching

</code_context>

<specifics>
## Specific Ideas

- Diagram must match m3ter's existing branded architecture diagrams: navy background (#1a1f36), white rounded card containers with subtle shadows, company logos, green m3ter accent, colored data flow pill labels, dashed connection lines with dot endpoints
- Connection type colors are locked: Native Connector = green, Webhook/API = blue, Custom Build = orange — applied via inline hex styles, not dynamic Tailwind classes (REND-03)
- m3ter hub node displays internal capability labels: Usage, Pricing, Rating, Credits, Alerts, Limits (COMP-05)
- Pure SVG rendering with inline styles — no foreignObject, no dynamic Tailwind classes (REND-03). This ensures clean export in Phase 4.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-rendering-engine*
*Context gathered: 2026-03-24*
