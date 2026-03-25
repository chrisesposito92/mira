# Phase 2: Rendering Engine - Research

**Researched:** 2026-03-24
**Domain:** SVG diagram rendering, hub-and-spoke layout algorithm, Svelte 5 SVG components
**Confidence:** HIGH

## Summary

Phase 2 builds a pure SVG diagram renderer inside the existing SvelteKit/Svelte 5 frontend. The renderer takes `DiagramContent` data (systems, connections, settings) from Phase 1's data model and produces a branded, m3ter-styled SVG canvas with hub-and-spoke layout. No third-party diagramming libraries are needed -- this is hand-built SVG using Svelte 5 components with `<svelte:options namespace="svg" />` for correct SVG namespace handling.

The core technical challenges are: (1) a zone-based auto-layout algorithm that positions nodes around a central m3ter hub, (2) SVG marker definitions for arrowheads and dots that inherit connection colors via `context-stroke`/`context-fill`, (3) reactive rendering via `$derived` that recomputes layout when diagram content changes, and (4) strict inline-style-only SVG output (no Tailwind classes, no `foreignObject`) to ensure clean export in Phase 4.

**Primary recommendation:** Build all SVG sub-components as Svelte 5 components with `namespace="svg"`, use a pure-function layout algorithm that outputs positioned coordinates, and define shared SVG `<defs>` (filters, markers) once in a top-level `SvgDefs.svelte` component. Use `context-stroke` for marker color inheritance to avoid per-connection-type marker duplication.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Zone-based layout -- prospect node ("Your Product/Platform") fixed at top-center, m3ter hub dead center, system categories arranged in clockwise zones (left, bottom-left, bottom, bottom-right, right)
- **D-02:** Fixed canvas with reflow -- single canvas size, nodes reposition and resize as system count grows. Export dimensions are predictable.
- **D-03:** Automatic zone assignment by category order -- `display_order` from the component library table drives clockwise zone fill. No user-assignable zones in v1.
- **D-04:** Straight dashed lines -- direct point-to-point SVG paths matching m3ter reference style. No curves or orthogonal routing.
- **D-05:** Midpoint pill labels -- data flow pill labels (colored rounded rectangles with text) centered on the connection line.
- **D-06:** Dot at source, arrowhead at target -- small filled circle at the origin end, arrowhead at the destination. Bidirectional connections get arrowheads at both ends (no dots).
- **D-07:** Logo grid -- systems inside a category group card render as small logo squares in rows (2-3 per row) with names below each logo.
- **D-08:** Text-only header -- category name in bold/muted text at the top of the white containing card. No colored bars or icons.
- **D-09:** Individual cards for standalone systems -- ungrouped systems, custom nodes, and single-system categories render as standalone white rounded cards with logo + name.
- **D-10:** Minimal dialog -- simple "Add Custom System" modal with name field + domain field, accessible from a "+" button on the diagram page.
- **D-11:** Live preview on domain blur -- when the domain field loses focus, the logo proxy is called and a preview shows the fetched logo (or monogram fallback).

### Claude's Discretion
- Exact canvas dimensions and SVG coordinate system
- Font choice -- Inter as default (per STATE.md: "if m3ter brand font unavailable, use Inter")
- Spacing constants, card dimensions, border radius, shadow styling
- Dashed line `stroke-dasharray` pattern and stroke width
- Logo grid column count per card width (2 vs 3 per row)
- Monogram SVG rendering (parsing `monogram:<INITIALS>:<COLOR>` format from Phase 1)
- DiagramStore reactive state extension for content editing
- SVG marker definitions for dots and arrowheads
- Exact pill label sizing, padding, font size

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REND-01 | Live preview updates in real-time as user configures | Svelte 5 `$derived` reactivity; layout algorithm as pure function recomputed on content change |
| REND-02 | Diagram renders in m3ter branded style (navy bg, white cards, logos, green accent, pills, dashed lines) | SVG inline styles with hex color constants from UI-SPEC; `feDropShadow` for card shadows |
| REND-03 | Pure SVG rendering with inline styles (no foreignObject, no dynamic Tailwind classes) | `<svelte:options namespace="svg" />` on all SVG sub-components; all styling via inline `style` attributes |
| REND-04 | Hub-and-spoke auto-layout algorithm with m3ter centered | Zone-based layout algorithm using trigonometric positioning (cos/sin for zone angles) |
| REND-05 | Grouped system categories render as containing cards with sub-items and multiple logos | GroupCard component with logo grid layout; dynamic height based on system count |
| COMP-02 | User can create custom system nodes with name and optional logo | AddCustomSystemDialog using shadcn Dialog + Input; logo proxy call on domain blur |
| COMP-04 | Customizable "Your Product/Platform" prospect node with editable name | ProspectNode component at fixed top-center position; name from DiagramContent |
| COMP-05 | m3ter hub node always present and centered, displaying internal capability labels | HubNode component at canvas center; 6 hardcoded capability labels |
| CONN-04 | Connections color-coded by integration type (green, blue, orange) | Inline hex color map keyed by `connection_type`; `context-stroke` for marker color inheritance |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Svelte 5 runes only** -- `$state`, `$derived`, `$effect`. No legacy `writable()`/`readable()` stores.
- **`lang="ts"` on all `<script>` blocks**
- **`cn()` from `$lib/utils`** for conditional class merging on application chrome elements (not SVG)
- **Tailwind v4 with CSS `@theme` variables** -- no `tailwind.config.js`
- **shadcn-svelte components in `$lib/components/ui/`** -- Dialog, Input, Button, Label, Skeleton confirmed available
- **Mode-watcher** for dark mode -- `ModeWatcher` in root layout
- **Import aliases**: `$lib`, `$components`, `$stores`, `$services`, `$types`
- **Test files co-located**: `*.test.ts` alongside source files
- **GSD workflow enforcement**: All edits go through GSD commands

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Svelte 5 | 5.55+ | Component framework | Already installed; runes reactivity drives live preview (REND-01) |
| SvelteKit 2 | 2.55+ | Routing framework | Already installed; provides `(app)/diagrams/[id]/` route |
| TypeScript 5.9 | 5.9 | Type safety | Already configured; strict mode |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shadcn-svelte | 1.1 | Dialog, Input, Button, Label, Skeleton | Application chrome only (AddCustomSystemDialog) |
| bits-ui | 2.16 | Headless primitives (Dialog internals) | Under shadcn-svelte; no direct usage |
| lucide-svelte | 0.575 | Icons (Plus for "Add Custom System" button) | Toolbar button icons |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-built SVG | D3.js | D3 adds 80KB+ bundle; overkill for static layout; SVG is simpler and better for export |
| Hand-built SVG | Cytoscape.js | Graph library with canvas rendering; incompatible with SVG export requirement |
| Hand-built SVG | Svelvet | Svelte flow library; too interactive/WYSIWYG; contradicts configurator decision |
| Pure function layout | dagre/ELK.js | Graph layout engines; overkill for fixed hub-and-spoke with 5 zones |

**No new packages needed.** Phase 2 uses zero new npm dependencies. All rendering is pure SVG within existing Svelte 5 components.

## Architecture Patterns

### Recommended Project Structure

```
frontend/src/lib/
├── components/diagram/
│   ├── index.ts                        # Re-exports (extend existing)
│   ├── DiagramCard.svelte              # Existing (Phase 1)
│   ├── CreateDiagramDialog.svelte      # Existing (Phase 1)
│   ├── DeleteDiagramDialog.svelte      # Existing (Phase 1)
│   ├── DiagramRenderer.svelte          # NEW: Top-level SVG renderer
│   ├── SvgDefs.svelte                  # NEW: Shared <defs> (filters, markers)
│   ├── AddCustomSystemDialog.svelte    # NEW: Custom node creation modal
│   ├── LogoPreview.svelte              # NEW: Logo fetch preview in dialog
│   ├── nodes/
│   │   ├── HubNode.svelte             # NEW: m3ter hub with capability labels
│   │   ├── ProspectNode.svelte        # NEW: "Your Product/Platform" top node
│   │   ├── SystemCard.svelte          # NEW: Individual system (logo + name)
│   │   ├── GroupCard.svelte           # NEW: Category group with logo grid
│   │   └── MonogramSvg.svelte         # NEW: Monogram fallback renderer
│   └── connections/
│       ├── ConnectionLine.svelte       # NEW: Dashed line with markers
│       └── ConnectionPill.svelte       # NEW: Colored pill label at midpoint
├── stores/
│   └── diagrams.svelte.ts              # EXTEND: Add currentDiagram, content editing
├── services/
│   └── diagrams.ts                     # NO CHANGE: Already has update(), listComponents()
├── types/
│   └── diagram.ts                      # EXTEND: Add layout types (LayoutResult, PositionedNode, etc.)
└── utils/
    └── diagram-layout.ts               # NEW: Pure layout algorithm function

frontend/src/routes/(app)/diagrams/
├── +page.svelte                        # Existing list page
├── +page.ts                            # Existing list loader
└── [id]/
    ├── +page.svelte                    # NEW: Diagram editor/preview page
    └── +page.ts                        # NEW: Load diagram + component library
```

### Pattern 1: SVG Namespace Components

**What:** Every Svelte component that renders SVG elements (not wrapping an `<svg>` tag, but rendering elements *inside* one) must declare `<svelte:options namespace="svg" />`. Without this, Svelte creates elements in the HTML namespace, causing silent rendering failures for SVG-specific elements like `<circle>`, `<rect>`, `<text>`, `<line>`, `<path>`, `<g>`, `<filter>`, `<marker>`.

**When to use:** All components in `diagram/nodes/`, `diagram/connections/`, `SvgDefs.svelte`, `MonogramSvg.svelte`.

**Exception:** `DiagramRenderer.svelte` creates the root `<svg>` element itself, so it renders in HTML namespace (the `<svg>` tag switches the browser into SVG namespace). Child components rendered inside it need `namespace="svg"`.

**Example:**
```svelte
<!-- Source: https://svelte.dev/docs/svelte/svelte-options -->
<svelte:options namespace="svg" />

<script lang="ts">
  let { cx, cy, r, label }: { cx: number; cy: number; r: number; label: string } = $props();
</script>

<g>
  <circle {cx} {cy} {r} fill="#FFFFFF" stroke="#00C853" stroke-width="3" />
  <text x={cx} y={cy} text-anchor="middle" dominant-baseline="central"
    style="font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 700; fill: #1E293B;">
    {label}
  </text>
</g>
```

### Pattern 2: Pure Function Layout Algorithm

**What:** The layout algorithm is a pure TypeScript function that takes `DiagramContent` + `ComponentLibraryItem[]` and returns `LayoutResult` with all positioned coordinates. No side effects, no DOM access. Easy to test, easy to derive reactively.

**When to use:** Called via `$derived` in DiagramRenderer whenever content changes.

**Example:**
```typescript
// Source: Custom implementation following D-01/D-02/D-03

export interface PositionedSystem {
  system: DiagramSystem;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface PositionedGroup {
  category: string;
  systems: PositionedSystem[];
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface LayoutResult {
  hub: { x: number; y: number };
  prospect: PositionedSystem;
  groups: PositionedGroup[];
  standalone: PositionedSystem[];
}

// In DiagramRenderer.svelte:
const layout = $derived(layoutDiagram(content, componentLibrary));
```

### Pattern 3: Inline SVG Styles Only (REND-03)

**What:** All SVG elements use inline `style` attributes with hex color values. No Tailwind utility classes, no CSS class references, no `foreignObject`. This ensures the SVG is self-contained for Phase 4 export.

**When to use:** Every SVG element inside the canvas.

**Example:**
```svelte
<!-- CORRECT: inline styles with hex values -->
<rect x={10} y={10} width={120} height={100} rx={12}
  style="fill: #FFFFFF; stroke: #E2E8F0; stroke-width: 1;"
  filter="url(#card-shadow)" />

<!-- WRONG: Tailwind classes (will not export) -->
<rect class="fill-white stroke-slate-200 rounded-xl" />

<!-- WRONG: foreignObject (will break export) -->
<foreignObject><div class="p-4">...</div></foreignObject>
```

### Pattern 4: Context-Stroke for Marker Color Inheritance

**What:** SVG markers (arrowheads, dots) use `context-stroke` and `context-fill` so a single marker definition works for all connection colors. The marker inherits the stroke color of the line it is attached to.

**When to use:** Marker definitions in SvgDefs.svelte.

**Browser support:** Chrome 124+ (April 2024), Firefox (long-standing), Safari 17.2+. All target browsers for desktop SEs are covered.

**Example:**
```svelte
<!-- Source: https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/marker -->
<defs>
  <!-- Arrowhead that inherits line color -->
  <marker id="arrowhead" viewBox="0 0 10 10" refX="10" refY="5"
    markerWidth="8" markerHeight="8" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
  </marker>

  <!-- Dot that inherits line color -->
  <marker id="dot" viewBox="0 0 10 10" refX="5" refY="5"
    markerWidth="8" markerHeight="8">
    <circle cx="5" cy="5" r="4" fill="context-stroke" />
  </marker>
</defs>

<!-- Usage on connection line: markers inherit #00C853 -->
<line x1={100} y1={200} x2={300} y2={400}
  style="stroke: #00C853; stroke-width: 2; stroke-dasharray: 6,4;"
  marker-start="url(#dot)" marker-end="url(#arrowhead)" />
```

**Fallback consideration:** If `context-stroke` proves unreliable during export (Phase 4), the fallback is to define separate marker IDs per connection type color (e.g., `arrowhead-native`, `arrowhead-webhook`, `arrowhead-custom`, `arrowhead-api`). This is 4 copies of each marker -- acceptable overhead.

### Pattern 5: DiagramStore Extension

**What:** Extend the existing `DiagramStore` class (singleton pattern) with content editing state rather than creating a separate store. Add `currentDiagram`, `componentLibrary`, `updateContent()`, and derived layout state.

**Example:**
```typescript
// Extend existing DiagramStore class
class DiagramStore {
  // ... existing list/create/delete state ...

  currentDiagram = $state<Diagram | null>(null);
  componentLibrary = $state<ComponentLibraryItem[]>([]);
  saving = $state(false);

  // Derived: systems grouped by category
  systemsByCategory = $derived.by(() => {
    if (!this.currentDiagram) return new Map();
    // group systems by category
  });

  async loadDiagram(service: DiagramService, id: string) { ... }
  async loadComponentLibrary(service: DiagramService) { ... }
  async updateContent(service: DiagramService, content: DiagramContent) { ... }
  addSystem(system: DiagramSystem) { ... }
  removeSystem(id: string) { ... }
}
```

### Anti-Patterns to Avoid

- **Dynamic Tailwind classes on SVG elements:** Tailwind classes will not survive export. Use inline `style` attributes exclusively.
- **`foreignObject` for text/HTML inside SVG:** Breaks many SVG renderers and export tools. Use native SVG `<text>` elements.
- **Separate "renderer store":** Splits state management. Extend the existing `DiagramStore` instead.
- **D3.js for simple layout:** Massive dependency for what is a straightforward coordinate calculation. Write a pure function.
- **Canvas-based rendering:** Incompatible with SVG export requirement (EXPO-02). Must be SVG.
- **`<svelte:element>` for SVG children:** Loses static analysis benefits. Use concrete SVG element tags.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dialog modal | Custom modal overlay | shadcn-svelte `Dialog` | Handles focus trap, backdrop, a11y, escape key |
| Form inputs | Custom input elements | shadcn-svelte `Input` + `Label` | Consistent with app chrome styling |
| Loading skeleton | Custom shimmer animation | shadcn-svelte `Skeleton` | Matches existing loading states |
| Drop shadow filter | Custom blur/offset chain | SVG `<feDropShadow>` primitive | Single element, standard spec, widely supported |
| Marker inheritance | Per-color marker copies | `context-stroke` / `context-fill` | DRY; one marker definition serves all colors |
| UUID generation | Custom random ID | `crypto.randomUUID()` | Browser native, already used in Phase 1 for client-side IDs |

**Key insight:** The SVG rendering itself IS hand-built (no library), but every SVG primitive (markers, filters, text) uses standard SVG spec elements rather than custom approximations. The application chrome (dialog, buttons, inputs) uses shadcn-svelte. The boundary is clear: SVG canvas = hand-built inline SVG; everything else = existing component library.

## Common Pitfalls

### Pitfall 1: Missing SVG Namespace on Svelte Components

**What goes wrong:** SVG elements render as empty HTML elements (invisible). No error in console.
**Why it happens:** Svelte defaults to HTML namespace. `<rect>`, `<circle>`, `<text>` etc. are created as HTMLUnknownElement instead of SVGElement.
**How to avoid:** Add `<svelte:options namespace="svg" />` to EVERY component that renders SVG children (not the one that creates the root `<svg>` tag).
**Warning signs:** Elements appear in DOM inspector but are invisible; `instanceof SVGElement` returns false.

### Pitfall 2: SVG Text Positioning

**What goes wrong:** Text appears misaligned or at wrong position.
**Why it happens:** SVG `<text>` positions from baseline by default, not top-left like HTML. Multi-line text needs manual `<tspan>` elements with `dy` offsets.
**How to avoid:** Use `text-anchor="middle"` for horizontal centering and `dominant-baseline="central"` or `dy` offsets for vertical centering. Test with different text lengths.
**Warning signs:** Text overflows card boundaries; text appears too low or too high within containers.

### Pitfall 3: SVG Filter Performance

**What goes wrong:** Diagram renders slowly with many cards, each using `filter="url(#card-shadow)"`.
**Why it happens:** SVG filters are expensive; each filter application triggers a separate rasterization pass.
**How to avoid:** Define the filter once in `<defs>` and reference by ID. Consider using `filterUnits="userSpaceOnUse"` with explicit `x`, `y`, `width`, `height` to limit the filter region. For performance, the shadow blur should be small (stdDeviation=4 or less).
**Warning signs:** Diagram becomes sluggish with 15+ cards; browser memory usage spikes.

### Pitfall 4: Marker Scaling with Stroke Width

**What goes wrong:** Arrowheads and dots appear too large or too small.
**Why it happens:** Default `markerUnits="strokeWidth"` scales markers proportionally to the line's stroke width. Since connection stroke-width is 2px, markers scaled by strokeWidth may be unexpectedly sized.
**How to avoid:** Use `markerUnits="userSpaceOnUse"` for absolute sizing, or carefully tune `markerWidth`/`markerHeight` relative to stroke-width. The ARROWHEAD_SIZE constant (8) and CONNECTION_DOT_RADIUS (4) from UI-SPEC should be in userSpaceOnUse coordinates.
**Warning signs:** Markers look different at different zoom levels; markers are invisible (too small) or dominate the line (too large).

### Pitfall 5: Base64 Image Rendering in SVG

**What goes wrong:** Logos stored as base64 data URLs don't appear in SVG `<image>` elements.
**Why it happens:** SVG `<image>` requires `href` (not `src`). Some older references use `xlink:href` which is deprecated. The `width` and `height` attributes are required (not optional like HTML `<img>`).
**How to avoid:** Use `<image href={logo_base64} width={LOGO_SIZE} height={LOGO_SIZE} />` with explicit dimensions. Ensure `preserveAspectRatio="xMidYMid meet"` for consistent scaling.
**Warning signs:** Empty rectangles where logos should be; logos stretched or cropped incorrectly.

### Pitfall 6: Monogram Parsing Edge Cases

**What goes wrong:** Monogram format `monogram:<INITIALS>:<COLOR>` fails to parse.
**Why it happens:** Color values may contain colons (unlikely but possible), initials may be empty or very long, or the field may be null.
**How to avoid:** Strict regex parsing: `/^monogram:([A-Z]{1,3}):(#[0-9A-Fa-f]{6})$/`. Guard against null/undefined `logo_base64`. Fallback to a default monogram (gray circle with "?") if parsing fails.
**Warning signs:** Uncaught exceptions in MonogramSvg component; blank spaces where monograms should appear.

### Pitfall 7: Layout Algorithm Zone Overflow

**What goes wrong:** With many systems, nodes overlap or extend beyond the canvas bounds.
**Why it happens:** Fixed 1200x800 canvas with no scrolling. Each zone has limited space; too many categories overflows the 5-zone arrangement.
**How to avoid:** Implement proportional scaling (D-02: "nodes reposition and resize as system count grows"). Calculate dynamic card sizes based on total system count. Cap LOGO_SIZE and GROUP_CARD_PADDING at smaller values when density is high. Define a MAX_SYSTEMS threshold where layout degradation becomes unacceptable (likely ~30-40 systems).
**Warning signs:** Cards overlap; text becomes unreadable at small sizes; layout algorithm produces NaN coordinates.

## Code Examples

Verified patterns from official sources:

### Hub-and-Spoke Zone Calculation

```typescript
// Source: Standard trigonometry for radial positioning
// Zone angles: left(180deg), bottom-left(225deg), bottom(270deg), bottom-right(315deg), right(0deg)

const ZONE_ANGLES: Record<string, number> = {
  right: 0,
  'bottom-right': Math.PI * 0.3,     // ~54 degrees below horizontal
  bottom: Math.PI * 0.5,              // 90 degrees (straight down)
  'bottom-left': Math.PI * 0.7,       // ~126 degrees
  left: Math.PI,                       // 180 degrees (straight left)
};

const ZONE_ORDER = ['left', 'bottom-left', 'bottom', 'bottom-right', 'right'];

function getZonePosition(
  zoneIndex: number,
  hubX: number,
  hubY: number,
  radius: number
): { x: number; y: number } {
  const zoneName = ZONE_ORDER[zoneIndex % ZONE_ORDER.length];
  const angle = ZONE_ANGLES[zoneName];
  return {
    x: hubX + Math.cos(angle) * radius,
    y: hubY + Math.sin(angle) * radius,
  };
}
```

### SVG Drop Shadow Filter Definition

```svelte
<!-- Source: https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDropShadow -->
<svelte:options namespace="svg" />

<defs>
  <!-- Card drop shadow: offset 0,2 with blur 4 -->
  <filter id="card-shadow" x="-10%" y="-10%" width="120%" height="130%">
    <feDropShadow dx="0" dy="2" stdDeviation="4"
      flood-color="rgba(0,0,0,0.15)" flood-opacity="1" />
  </filter>
</defs>
```

### SVG Marker Definitions (Arrowhead + Dot)

```svelte
<!-- Source: https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/marker -->
<svelte:options namespace="svg" />

<defs>
  <!-- Arrowhead marker: inherits connection line color -->
  <marker id="arrowhead"
    viewBox="0 0 10 10"
    refX="10" refY="5"
    markerWidth="8" markerHeight="8"
    orient="auto-start-reverse"
    markerUnits="userSpaceOnUse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
  </marker>

  <!-- Source dot marker: inherits connection line color -->
  <marker id="source-dot"
    viewBox="0 0 10 10"
    refX="5" refY="5"
    markerWidth="8" markerHeight="8"
    markerUnits="userSpaceOnUse">
    <circle cx="5" cy="5" r="4" fill="context-stroke" />
  </marker>
</defs>
```

### Connection Type Color Map

```typescript
// Source: CONTEXT.md D-04, UI-SPEC color table, CONN-04

export const CONNECTION_COLORS: Record<string, string> = {
  native_connector: '#00C853',
  webhook_api: '#2196F3',
  custom_build: '#FF9800',
  api: '#90A4AE',
} as const;
```

### Monogram Parser

```typescript
// Source: Phase 1 D-08, format: monogram:<INITIALS>:<COLOR>

const MONOGRAM_RE = /^monogram:([A-Z]{1,3}):(#[0-9A-Fa-f]{6})$/;

export function parseMonogram(logo_base64: string | null): {
  initials: string;
  color: string;
} | null {
  if (!logo_base64) return null;
  const match = logo_base64.match(MONOGRAM_RE);
  if (!match) return null;
  return { initials: match[1], color: match[2] };
}
```

### Connection Pill Midpoint Calculation

```typescript
// Source: Standard midpoint formula

export function getConnectionMidpoint(
  x1: number, y1: number, x2: number, y2: number
): { x: number; y: number } {
  return {
    x: (x1 + x2) / 2,
    y: (y1 + y2) / 2,
  };
}

// Pill dimensions depend on text width -- measure with canvas or estimate
export function estimatePillWidth(text: string, fontSize: number): number {
  // Approximate: average character width is ~0.6 * fontSize for Inter medium
  return text.length * fontSize * 0.6 + PILL_PADDING_X * 2;
}
```

### DiagramRenderer Top-Level Structure

```svelte
<!-- DiagramRenderer.svelte -- renders in HTML namespace (creates <svg>) -->
<script lang="ts">
  import type { DiagramContent, ComponentLibraryItem } from '$types';
  import { layoutDiagram } from '$lib/utils/diagram-layout.js';
  import SvgDefs from './SvgDefs.svelte';
  import HubNode from './nodes/HubNode.svelte';
  import ProspectNode from './nodes/ProspectNode.svelte';
  import GroupCard from './nodes/GroupCard.svelte';
  import SystemCard from './nodes/SystemCard.svelte';
  import ConnectionLine from './connections/ConnectionLine.svelte';
  import { CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_BG } from './constants.js';

  let {
    content,
    componentLibrary,
  }: {
    content: DiagramContent;
    componentLibrary: ComponentLibraryItem[];
  } = $props();

  const layout = $derived(layoutDiagram(content, componentLibrary));
</script>

<svg
  viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}"
  xmlns="http://www.w3.org/2000/svg"
  style="background: {CANVAS_BG}; width: 100%; height: auto;"
>
  <SvgDefs />

  <!-- Connections drawn first (behind nodes) -->
  {#each content.connections as conn (conn.id)}
    <ConnectionLine connection={conn} {layout} />
  {/each}

  <!-- Hub node (center) -->
  <HubNode x={layout.hub.x} y={layout.hub.y} />

  <!-- Prospect node (top) -->
  <ProspectNode system={layout.prospect} />

  <!-- Grouped categories -->
  {#each layout.groups as group (group.category)}
    <GroupCard {group} />
  {/each}

  <!-- Standalone systems -->
  {#each layout.standalone as system (system.system.id)}
    <SystemCard positioned={system} />
  {/each}
</svg>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `xlink:href` on SVG `<image>` | `href` attribute (no xlink namespace) | SVG 2 spec; all browsers since ~2020 | Use `href` not `xlink:href` |
| Per-color marker definitions | `context-stroke`/`context-fill` in markers | Chrome 124 (April 2024), Safari 17.2, Firefox (long-standing) | Single marker definition for all colors |
| `<feGaussianBlur>` + `<feOffset>` + `<feMerge>` for shadows | `<feDropShadow>` shorthand | Widely available since Jan 2020 | Simpler filter definition |
| Svelte 3/4 `writable()` stores | Svelte 5 `$state` + `$derived` runes | Svelte 5.0 (Oct 2024) | All state management uses runes |
| `namespace="svg"` in svelte.config.js | `<svelte:options namespace="svg" />` per component | Svelte 5 | Component-level namespace declaration |

**Deprecated/outdated:**
- `xlink:href`: Use `href` directly on `<image>` elements
- `writable()`/`readable()`: Replaced by `$state`/`$derived` runes
- Global SVG namespace in svelte.config.js: Now per-component via `<svelte:options>`

## Open Questions

1. **m3ter Brand Font**
   - What we know: STATE.md says "if m3ter brand font unavailable, use Inter". UI-SPEC specifies Inter as default.
   - What's unclear: Whether m3ter has a custom brand font file available for use.
   - Recommendation: Use Inter throughout. It is a widely available, high-quality sans-serif. Phase 4 will inline it as base64 for export consistency. This is a safe default that can be swapped later.

2. **context-stroke Export Compatibility**
   - What we know: `context-stroke` works in all modern browsers for live rendering. Phase 4 uses `html-to-image` for PNG export.
   - What's unclear: Whether `html-to-image@1.11.11` correctly handles `context-stroke` in SVG markers when converting to canvas.
   - Recommendation: Build with `context-stroke` for live rendering (DRY, elegant). If Phase 4 testing reveals export issues, the fallback (per-color marker IDs) is a small refactor localized to `SvgDefs.svelte` and `ConnectionLine.svelte`.

3. **Maximum System Count**
   - What we know: Canvas is fixed at 1200x800. 5 zones around the hub. Typical SE diagrams have 8-15 systems.
   - What's unclear: At what count the layout algorithm produces unreadable output.
   - Recommendation: Design for 20-25 systems comfortably. Add proportional scaling at 15+ systems. Document the practical limit (likely ~35-40) and flag for user testing.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 4.0 + @testing-library/svelte |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npx vitest run` |
| Full suite command | `cd frontend && npx vitest run` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REND-01 | Layout recomputes when content changes | unit | `cd frontend && npx vitest run src/lib/utils/diagram-layout.test.ts -x` | Wave 0 |
| REND-02 | SVG uses correct hex colors from design spec | unit | `cd frontend && npx vitest run src/lib/components/diagram/DiagramRenderer.svelte.test.ts -x` | Wave 0 |
| REND-03 | No Tailwind classes or foreignObject in SVG output | unit | `cd frontend && npx vitest run src/lib/components/diagram/DiagramRenderer.svelte.test.ts -x` | Wave 0 |
| REND-04 | Hub at center, prospect at top, zones positioned correctly | unit | `cd frontend && npx vitest run src/lib/utils/diagram-layout.test.ts -x` | Wave 0 |
| REND-05 | Group cards contain multiple systems with logos | unit | `cd frontend && npx vitest run src/lib/components/diagram/nodes/GroupCard.svelte.test.ts -x` | Wave 0 |
| COMP-02 | AddCustomSystemDialog calls logo proxy, adds system | unit | `cd frontend && npx vitest run src/lib/components/diagram/AddCustomSystemDialog.svelte.test.ts -x` | Wave 0 |
| COMP-04 | Prospect node renders with customizable name | unit | `cd frontend && npx vitest run src/lib/components/diagram/nodes/ProspectNode.svelte.test.ts -x` | Wave 0 |
| COMP-05 | Hub node shows all 6 capability labels | unit | `cd frontend && npx vitest run src/lib/components/diagram/nodes/HubNode.svelte.test.ts -x` | Wave 0 |
| CONN-04 | Connection lines use correct hex colors per type | unit | `cd frontend && npx vitest run src/lib/components/diagram/connections/ConnectionLine.svelte.test.ts -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `cd frontend && npx vitest run`
- **Per wave merge:** `cd frontend && npx vitest run`
- **Phase gate:** Full suite green (currently 125 tests + new Phase 2 tests)

### Wave 0 Gaps

- [ ] `src/lib/utils/diagram-layout.test.ts` -- covers REND-01, REND-04 (pure function, most testable)
- [ ] `src/lib/components/diagram/DiagramRenderer.svelte.test.ts` -- covers REND-02, REND-03
- [ ] `src/lib/components/diagram/nodes/HubNode.svelte.test.ts` -- covers COMP-05
- [ ] `src/lib/components/diagram/nodes/ProspectNode.svelte.test.ts` -- covers COMP-04
- [ ] `src/lib/components/diagram/nodes/GroupCard.svelte.test.ts` -- covers REND-05
- [ ] `src/lib/components/diagram/connections/ConnectionLine.svelte.test.ts` -- covers CONN-04
- [ ] `src/lib/components/diagram/AddCustomSystemDialog.svelte.test.ts` -- covers COMP-02
- [ ] `src/lib/stores/diagrams.svelte.test.ts` -- covers store extension (currentDiagram, updateContent)

## Sources

### Primary (HIGH confidence)

- Svelte 5 docs (`<svelte:options namespace="svg" />`) -- https://svelte.dev/docs/svelte/svelte-options
- MDN SVG `<marker>` element -- https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/marker
- MDN SVG `<feDropShadow>` -- https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDropShadow
- MDN SVG Positions tutorial -- https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Positions
- MDN SVG Paths tutorial -- https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Paths
- Phase 1 data model (`backend/app/schemas/diagrams.py`, `frontend/src/lib/types/diagram.ts`) -- verified by reading source
- Phase 1 services (`frontend/src/lib/services/diagrams.ts`) -- verified `update()` and `listComponents()` exist
- Phase 1 store (`frontend/src/lib/stores/diagrams.svelte.ts`) -- verified singleton pattern, ready for extension
- Existing route pattern (`frontend/src/routes/(app)/diagrams/+page.ts`) -- verified load function pattern

### Secondary (MEDIUM confidence)

- SVG `context-stroke`/`context-fill` browser support -- https://www.roboleary.net/2024/05/10/svg-context-fill-stroke (Chrome 124+, verified via chromestatus)
- Hub-and-spoke layout math (trigonometric positioning) -- https://kevinhoyt.com/blog/2025/07/15/comfort-w-circles/
- SVG marker styling patterns -- https://gist.github.com/kenpenn/8d782030e4be9d832be7

### Tertiary (LOW confidence)

- None -- all critical claims verified against official documentation or source code.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies; all rendering uses native SVG + existing Svelte 5
- Architecture: HIGH -- verified existing code patterns; SVG namespace handling confirmed in Svelte docs
- Pitfalls: HIGH -- SVG rendering pitfalls well-documented in MDN; namespace issue verified empirically
- Layout algorithm: MEDIUM -- zone-based positioning is straightforward math, but exact spacing constants need tuning during implementation

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable domain; SVG spec and Svelte 5 runes API are mature)
