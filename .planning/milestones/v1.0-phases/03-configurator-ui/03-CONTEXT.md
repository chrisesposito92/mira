# Phase 3: Configurator UI - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

A full builder UI where an SE can assemble a complete integration architecture diagram through form-driven sidebar panels, see a live SVG preview update in real-time, and have changes persist automatically via debounced auto-save with thumbnail generation. Includes: system picker with component library browsing, connection creation form with direction/type/label, auto-save with save status indicator, and diagram list enhancements (thumbnail, last-edited timestamp).

**Requirements in scope:** CONN-01, CONN-02, CONN-03, CONN-05, CONN-06, PERS-02, PERS-03, PERS-04, PERS-05

</domain>

<decisions>
## Implementation Decisions

### Builder Layout
- **D-01:** Left sidebar + right preview layout. Fixed-width sidebar (~360px) on the left, live DiagramRenderer preview fills remaining space on the right. Standard configurator pattern.
- **D-02:** Sidebar organized with shadcn Tabs component — three tabs: Systems, Connections, Settings.
- **D-03:** Fixed-width sidebar (not resizable). Consistent with the control panel pattern in the existing MIRA codebase.
- **D-04:** Subtle inline save status indicator in the header bar — small text/icon near the title showing "Saving...", "Saved", or a checkmark. Not toast-based for auto-save events.

### System Picker (Systems Tab)
- **D-05:** Category accordion with search bar at top. Expandable category sections show systems as clickable items with logos. Click to add system to the diagram. Component library's `category` and `display_order` drive the grouping and ordering.
- **D-06:** Already-added systems appear dimmed with a checkmark badge in the picker. Clicking them does nothing (prevents duplicates).
- **D-07:** Each system currently on the diagram has a remove button (small 'x' or remove action) in the Systems tab. Removal is sidebar-only — no SVG preview interaction needed.
- **D-08:** "Add Custom System" button at the bottom of the Systems tab opens the existing `AddCustomSystemDialog` from Phase 2.

### Connection Form (Connections Tab)
- **D-09:** Form-based connection creation, inline within the Connections tab. "Add Connection" button expands an inline form; connection list scrolls below. No dialog/modal.
- **D-10:** Connection form fields: source dropdown, target dropdown, direction toggle (unidirectional/bidirectional), integration type selector (native_connector, webhook_api, custom_build, api), label text input with suggestions.
- **D-11:** CONN-06 auto-suggest: When one end of the connection is m3ter and the other is a system with `is_native_connector = true`, the type selector auto-selects "Native Connector". SE can override.
- **D-12:** CONN-05 category-based label suggestions: Suggestion list derived from the source system's category (e.g., CRM systems suggest "Customer Data", "Usage Events"; Billing systems suggest "Invoice Data", "Payment Events"). SE can type a custom label.
- **D-13:** Connection list shows each connection with source→target names, type badge, label text, and Edit/Delete actions.

### Auto-Save (PERS-04)
- **D-14:** Reactive `$effect` watches `currentDiagram.content` for changes, debounces 500ms, then calls `updateContent()`. Must skip initial load to avoid unnecessary save on page entry.
- **D-15:** Save status shown via inline indicator (D-04), not toasts. Toasts reserved for errors only.

### Thumbnail Generation (PERS-05)
- **D-16:** Client-side SVG-to-canvas snapshot. After auto-save, serialize the current SVG element to a small canvas, export as base64 PNG, include in the save payload as `thumbnail_base64`. All client-side, no server rendering.

### Diagram List Enhancements (PERS-02, PERS-03)
- **D-17:** DiagramCard shows: thumbnail image at top (from `thumbnail_base64`), customer name, title (if different), last-edited relative timestamp (e.g., "2 hours ago"). Click navigates to the editor.
- **D-18:** PERS-03: Clicking a DiagramCard opens `/diagrams/[id]` editor route — the existing route from Phase 2, now upgraded with the full builder UI.

### Claude's Discretion
- Exact sidebar width (in the ~340-380px range)
- Tab icon choices (Lucide icons for Systems/Connections/Settings tabs)
- Category accordion expand/collapse behavior (single vs multi-expand)
- Search bar implementation (client-side filter of component library)
- Debounce utility implementation (custom vs library)
- SVG-to-canvas thumbnail resolution and size
- Relative timestamp formatting approach (Intl.RelativeTimeFormat or simple helper)
- Category-based suggestion map content (exact labels per category)
- Connection form validation rules (e.g., prevent self-connections, duplicate connections)
- Settings tab content (likely background color toggle, show/hide labels — from DiagramSettings type)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 2 Output (renderer and store)
- `frontend/src/lib/components/diagram/DiagramRenderer.svelte` — The SVG renderer component that receives `content` and `componentLibrary` props. Phase 3 wires it as the live preview.
- `frontend/src/lib/components/diagram/constants.ts` — SVG layout constants, colors, dimensions used by the renderer.
- `frontend/src/lib/components/diagram/index.ts` — Barrel export for all diagram components.
- `frontend/src/lib/stores/diagrams.svelte.ts` — DiagramStore with `currentDiagram`, `addSystem()`, `updateContent()`, `clearEditor()`, `componentLibrary`. Phase 3 extends this with removeSystem(), addConnection(), removeConnection(), updateConnection(), and auto-save logic.
- `frontend/src/lib/services/diagrams.ts` — DiagramService factory with `list()`, `get()`, `create()`, `update()`, `delete()`, `listComponents()`.
- `frontend/src/lib/types/diagram.ts` — All diagram types: DiagramSystem, DiagramConnection, DiagramContent, DiagramSettings, Diagram, DiagramListItem, DiagramCreate, DiagramUpdate, ComponentLibraryItem, LayoutResult, NodePositionMap.

### Existing Editor Route (Phase 2)
- `frontend/src/routes/(app)/diagrams/[id]/+page.svelte` — Current minimal editor. Phase 3 replaces the layout with sidebar + preview.
- `frontend/src/routes/(app)/diagrams/[id]/+page.ts` — Route load function fetching diagram and components.
- `frontend/src/routes/(app)/diagrams/+page.svelte` — Diagram list page with DiagramCard grid. Phase 3 enhances DiagramCard with thumbnail and last-edited timestamp.

### Existing Components to Reuse
- `frontend/src/lib/components/diagram/AddCustomSystemDialog.svelte` — Custom system creation dialog (D-08 reuses this).
- `frontend/src/lib/components/diagram/DiagramCard.svelte` — List card component. Phase 3 enhances with thumbnail and metadata.
- `frontend/src/lib/components/ui/` — shadcn-svelte: Tabs, Button, Input, Select, Card, Badge, Collapsible (for accordion), Dialog.

### Backend API (Phase 1)
- `backend/app/api/diagrams.py` — CRUD endpoints including PATCH for content updates (auto-save target).
- Component library endpoint (`GET /api/component-library`) — Returns systems with `category`, `is_native_connector`, `display_order`.

### Project Documentation
- `.planning/PROJECT.md` — Configurator-over-WYSIWYG decision, core constraints.
- `.planning/REQUIREMENTS.md` — Full requirement list. Phase 3: CONN-01 through CONN-06, PERS-02 through PERS-05.
- `.planning/phases/01-data-foundation/01-CONTEXT.md` — D-04: `is_native_connector` flag for CONN-06.
- `.planning/phases/02-rendering-engine/02-CONTEXT.md` — Layout algorithm decisions, connection rendering, DiagramStore extension patterns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DiagramStore` (`stores/diagrams.svelte.ts`) — Already has `addSystem()`, `updateContent()`, `loadComponentLibrary()`. Extend with `removeSystem()`, `addConnection()`, `removeConnection()`, `updateConnection()`.
- `DiagramRenderer` (`components/diagram/DiagramRenderer.svelte`) — Live SVG preview. Receives `content` and `componentLibrary` props. Renders reactively via `$derived`.
- `AddCustomSystemDialog` — Reuse as-is for custom system creation from the Systems tab.
- `DiagramCard` (`components/diagram/DiagramCard.svelte`) — Enhance with thumbnail display and last-edited timestamp.
- shadcn-svelte `Tabs`, `Collapsible`, `Select`, `Input`, `Button`, `Badge` — All available for the sidebar UI.
- `cn()` utility — For conditional class merging throughout.
- `EmptyState` component — Reusable for empty connection list state.

### Established Patterns
- Svelte 5 runes (`$state`, `$derived`, `$effect`) — All reactive state, including the auto-save `$effect`.
- Class-based store singleton — DiagramStore pattern; extend rather than create new stores.
- Factory function services (`createDiagramService(client)`) — No new service needed; existing service covers all endpoints.
- Service built in component via `$derived.by()` — Pattern established in Phase 2 editor page.

### Integration Points
- `frontend/src/routes/(app)/diagrams/[id]/+page.svelte` — Replace current minimal layout with sidebar + preview builder.
- `frontend/src/routes/(app)/diagrams/+page.svelte` — DiagramCard grid; cards get thumbnail + last-edited.
- `frontend/src/lib/stores/diagrams.svelte.ts` — Add removeSystem, connection CRUD methods, auto-save `$effect`.
- `frontend/src/lib/types/diagram.ts` — May need additional types for suggestion maps or form state.

</code_context>

<specifics>
## Specific Ideas

- The sidebar tab structure (Systems / Connections / Settings) matches the natural SE workflow: add systems first, then connect them, then adjust settings.
- Connection form auto-suggests "Native Connector" type when m3ter is one end and the other system has `is_native_connector = true` — this is a key UX differentiator.
- Category-based label suggestions reduce typing for common data flows while still allowing freeform labels.
- Thumbnail generation uses the existing SVG renderer output — no duplicate rendering needed, just canvas serialization of the existing DOM element.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-configurator-ui*
*Context gathered: 2026-03-24*
