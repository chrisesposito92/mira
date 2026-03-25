# Phase 4: Export Pipeline - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

An SE can export a finished diagram as a high-quality PNG or SVG suitable for slides and proposals. Includes: export service (SVG serialization, canvas-based PNG rendering), font inlining for consistent text rendering, file download trigger, and export UI in the diagram builder header.

**Requirements in scope:** EXPO-01, EXPO-02, EXPO-03, EXPO-04

</domain>

<decisions>
## Implementation Decisions

### Export Trigger UX
- **D-01:** Header toolbar dropdown — a single "Export" button in the DiagramBuilder header bar (next to back arrow and save indicator). Clicking opens a dropdown with "Export as PNG" and "Export as SVG".
- **D-02:** Instant download — click triggers the download immediately, no spinner or progress bar. Export should complete sub-second given the inline-style SVG pipeline.
- **D-03:** Export disabled when empty — dropdown only activates when at least one system node exists in the diagram. Disabled state shows tooltip explaining why.

### Font Inlining (EXPO-04)
- **D-04:** Embed Inter as base64 @font-face — bundle Inter woff2 as a static asset in the frontend. At export time, read it, base64-encode it, and inject an @font-face rule into the SVG's `<style>` block. PNG export inherits the font via the canvas rendering pipeline.
- **D-05:** Regular (400) weight only — the SVG renderer uses regular weight for all text (system names, labels, hub capabilities, connection pills). One woff2 file, ~90KB overhead per export.

### File Naming
- **D-06:** Customer name as filename — slugified `customer_name` field: "Acme Corp" → `acme-corp.png`. Falls back to diagram title if customer name is empty, then to `integration-diagram` as a generic fallback.

### PNG Export (EXPO-01)
- **D-07:** Always 2x resolution — export at 2400×1600 (2x the 1200×800 canvas). No resolution picker UI. Sharp on Retina displays and in presentation slides.
- **D-08:** Native Canvas API — use the same XMLSerializer → Image → Canvas pattern already proven in thumbnail generation code. Scale canvas to 2x. Zero new dependencies (no html-to-image library needed).

### SVG Export (EXPO-02)
- **D-09:** Serialize SVG with embedded font — XMLSerializer captures the SVG element, inject the @font-face style block, output as a downloadable .svg file. All logos are already base64 data URLs (from Phase 1 logo proxy), so EXPO-03 is satisfied by the existing architecture.

### Claude's Discretion
- Export service architecture (standalone utility vs. store method vs. component-level function)
- Exact dropdown component choice (shadcn DropdownMenu or custom)
- SVG `<style>` injection approach (prepend to existing SVG or wrapper)
- Slugify implementation for filename generation
- Download trigger mechanism (Blob URL + anchor click vs. other)
- Error handling for edge cases (canvas security errors, font load failures)
- Whether to preload the font file at page load or lazy-load at export time

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Export-Adjacent Code
- `frontend/src/lib/components/diagram/DiagramBuilder.svelte` lines 111-142 — `generateAndPersistThumbnail()` function: proven XMLSerializer → Blob → Image → Canvas → toDataURL pipeline. Export service should mirror this at 2x scale.
- `frontend/src/lib/components/diagram/DiagramRenderer.svelte` — The SVG element to serialize. Uses `role="img"` attribute for DOM selection. Pure inline styles, no foreignObject.
- `frontend/src/lib/components/diagram/SvgDefs.svelte` — Shared SVG defs (shadow filter, arrowhead marker, source dot marker). Must be included in serialized output.
- `frontend/src/lib/components/diagram/constants.ts` — `CANVAS_WIDTH` (1200), `CANVAS_HEIGHT` (800), `SVG_FONT_FAMILY`, all color constants.

### DiagramBuilder Header (integration point)
- `frontend/src/lib/components/diagram/DiagramBuilder.svelte` lines 1-30 — Header bar with back button, customer name, save indicator. Export button goes here.
- `frontend/src/lib/stores/diagrams.svelte.ts` — DiagramStore with `currentDiagram` (has `customer_name`, `title` for filename generation).

### Phase 1-3 Decisions Affecting Export
- `.planning/phases/01-data-foundation/01-CONTEXT.md` D-06/D-07 — Logos cached as base64 in DB, pre-fetched during seed. Canvas taint mitigated at source (EXPO-03).
- `.planning/phases/02-rendering-engine/02-CONTEXT.md` D-02 — Fixed canvas with predictable export dimensions.
- `.planning/phases/02-rendering-engine/02-CONTEXT.md` specifics — Pure SVG with inline styles, no foreignObject, no dynamic Tailwind (REND-03). Three-layer rendering for clean export.

### shadcn-svelte Components
- `frontend/src/lib/components/ui/dropdown-menu/` — DropdownMenu component for export button.
- `frontend/src/lib/components/ui/button/` — Button component for the trigger.
- `frontend/src/lib/components/ui/tooltip/` — Tooltip for disabled state explanation.

### Project Documentation
- `.planning/REQUIREMENTS.md` — EXPO-01 through EXPO-04 definitions.
- `.planning/PROJECT.md` — "Export to image only (no interactive HTML)" decision.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `generateAndPersistThumbnail()` in DiagramBuilder.svelte — The exact pattern needed for PNG export, just at thumbnail resolution (300×200). Export scales this to 2400×1600.
- `XMLSerializer` usage — Already serializes the SVG element for thumbnails. Same serialization needed for SVG export (with font injection).
- `DiagramStore.currentDiagram` — Has `customer_name` and `title` fields needed for filename generation.
- `document.querySelector('svg[role="img"]')` — Existing DOM selection pattern for the SVG element.
- shadcn-svelte `DropdownMenu` — Available in `$lib/components/ui/dropdown-menu/`.

### Established Patterns
- Svelte 5 runes (`$state`, `$derived`) — Export state (exporting, disabled) should use reactive state.
- Service built in component via `$derived.by()` — Pattern from DiagramBuilder.
- Lucide icons for UI consistency — `Download`, `Image`, `FileCode` available for dropdown items.

### Integration Points
- DiagramBuilder header bar — Export button added alongside existing back/save elements.
- DiagramStore — Provides `currentDiagram` for filename and empty-state check.
- `frontend/public/` or `frontend/src/lib/assets/` — Static location for bundled Inter woff2 font file.

</code_context>

<specifics>
## Specific Ideas

- The thumbnail code in DiagramBuilder.svelte is essentially a working prototype of the PNG export pipeline. The export service can extract and generalize this pattern.
- All logos are already base64 data URLs from the component library (Phase 1) — EXPO-03 (pre-fetch logos) is effectively solved by the existing architecture. The export service just needs to serialize the SVG as-is.
- STATE.md had a concern: "Verify base64 font injection approach works with html-to-image@1.11.11 before full ExportService build" — this is resolved: we're using native Canvas API (not html-to-image) and embedding Inter via @font-face in the SVG style block.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-export-pipeline*
*Context gathered: 2026-03-25*
