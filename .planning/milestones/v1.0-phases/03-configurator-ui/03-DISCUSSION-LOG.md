# Phase 3: Configurator UI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 03-configurator-ui
**Areas discussed:** Builder layout, System picker, Connection form, Auto-save & list

---

## Builder Layout

### Page layout structure

| Option | Description | Selected |
|--------|-------------|----------|
| Left sidebar + preview | Fixed-width left panel with tabs for System Picker / Connections / Settings. Preview fills remaining space. Standard configurator pattern. | ✓ |
| Right sidebar + preview | Same concept but panel on the right side. Preview on the left. | |
| Collapsible sidebar | Sidebar that can be collapsed to icon-only rail, giving preview full width. | |

**User's choice:** Left sidebar + preview
**Notes:** Standard configurator pattern matches the project's existing control panel approach.

### Sidebar content organization

| Option | Description | Selected |
|--------|-------------|----------|
| Tabs | shadcn Tabs component with 3 tabs: Systems, Connections, Settings. Each tab shows its panel content. | ✓ |
| Stacked accordion | All sections visible in scrollable sidebar with collapsible headers. | |
| You decide | Claude picks based on content density and interaction patterns. | |

**User's choice:** Tabs
**Notes:** None

### Sidebar sizing

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed width | Fixed at ~360px. Simple, predictable. Matches control panel pattern. | ✓ |
| Resizable | User can drag divider to resize sidebar vs preview. | |

**User's choice:** Fixed width
**Notes:** None

### Save status indicator

| Option | Description | Selected |
|--------|-------------|----------|
| Subtle inline indicator | Small text or icon near title: 'Saving...', 'Saved', or checkmark. Non-intrusive. | ✓ |
| Toast notifications | Use svelte-sonner toasts for save/error events. | |
| You decide | Claude picks based on auto-save frequency and UX. | |

**User's choice:** Subtle inline indicator
**Notes:** None

---

## System Picker

### Component library browsing pattern

| Option | Description | Selected |
|--------|-------------|----------|
| Category accordion + search | Search bar at top, expandable category sections below. Click to add. 'Add Custom' button at bottom. | ✓ |
| Flat grid with filter | All systems in scrollable grid with logo tiles. Category filter dropdown at top. | |
| You decide | Claude picks based on component library structure. | |

**User's choice:** Category accordion + search
**Notes:** None

### Already-added system appearance

| Option | Description | Selected |
|--------|-------------|----------|
| Dimmed with checkmark | Already-added systems show check badge and are visually muted. Prevents duplicates. | ✓ |
| Hidden entirely | Systems already on diagram removed from picker list. | |
| Always clickable | No visual distinction. Can add duplicates. | |

**User's choice:** Dimmed with checkmark
**Notes:** None

### System removal method

| Option | Description | Selected |
|--------|-------------|----------|
| Remove button in sidebar | Each system on diagram has small remove action in Systems tab. | ✓ |
| Context menu on preview | Right-click or hover node in SVG preview for remove option. | |
| Both | Remove from sidebar AND hover action on preview node. | |

**User's choice:** Remove button in sidebar
**Notes:** None

---

## Connection Form

### Connection creation method

| Option | Description | Selected |
|--------|-------------|----------|
| Form-based in sidebar | Connections tab has 'Add Connection' button with inline form: source/target dropdowns, direction, type, label. | ✓ |
| Click-to-connect on preview | Click source node in SVG → click target → form populates. | |
| Hybrid with highlighting | Dropdowns in form, hovering highlights corresponding node in preview. | |

**User's choice:** Form-based in sidebar
**Notes:** Clean configurator approach matching project philosophy.

### Data flow label suggestions (CONN-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Category-based suggestions | Suggestions derived from source system's category. | ✓ |
| Static per-system map | Hardcoded suggestions for specific system pairs. | |
| Free text only | No suggestions — SE types whatever they want. | |
| You decide | Claude picks best approach for coverage vs maintenance. | |

**User's choice:** Category-based suggestions
**Notes:** None

### Connection form style

| Option | Description | Selected |
|--------|-------------|----------|
| Inline in tab | Form expands inline within Connections tab. Connection list scrolls below. | ✓ |
| Dialog/modal | Opens shadcn Dialog for connection creation. | |
| You decide | Claude picks based on sidebar constraints. | |

**User's choice:** Inline in tab
**Notes:** None

---

## Auto-save & List

### Auto-save trigger mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| $effect + debounce | Reactive $effect watches content, debounces 500ms, saves. Catches all mutations. | ✓ |
| Explicit per-mutation | Each store method calls shared debounced save function. | |
| You decide | Claude picks cleanest approach for Svelte 5 runes. | |

**User's choice:** $effect + debounce
**Notes:** None

### Thumbnail generation (PERS-05)

| Option | Description | Selected |
|--------|-------------|----------|
| SVG-to-canvas snapshot | Client-side: serialize SVG to canvas, export as base64 PNG. | ✓ |
| Server-side rendering | Backend renders thumbnail via headless SVG renderer. | |
| No thumbnail for now | Skip PERS-05, add later. | |
| You decide | Claude picks based on SVG architecture. | |

**User's choice:** SVG-to-canvas snapshot
**Notes:** None

### Diagram list card display

| Option | Description | Selected |
|--------|-------------|----------|
| Thumbnail + metadata | Card shows thumbnail image, customer name, title, last-edited timestamp. | ✓ |
| Metadata only | No thumbnail — just customer name, title, and timestamp. | |
| You decide | Claude picks based on available data. | |

**User's choice:** Thumbnail + metadata
**Notes:** None

---

## Claude's Discretion

- Exact sidebar width (in the ~340-380px range)
- Tab icon choices (Lucide icons)
- Category accordion expand/collapse behavior
- Search bar implementation details
- Debounce utility implementation
- SVG-to-canvas thumbnail resolution and size
- Relative timestamp formatting approach
- Category-based suggestion map content
- Connection form validation rules
- Settings tab content

## Deferred Ideas

None — discussion stayed within phase scope.
