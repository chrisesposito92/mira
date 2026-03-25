# Phase 3: Configurator UI - Research

**Researched:** 2026-03-24
**Domain:** SvelteKit form-driven configurator UI, Svelte 5 runes reactivity, shadcn-svelte component composition, debounced auto-save, SVG-to-canvas thumbnail generation
**Confidence:** HIGH

## Summary

Phase 3 transforms the minimal diagram editor (Phase 2) into a full configurator-style builder with a left sidebar (360px fixed) containing three tabs (Systems, Connections, Settings) and a right-side live DiagramRenderer preview. The work is entirely frontend with one small backend adjustment (adding `thumbnail_base64` to the list response). All decisions are locked in CONTEXT.md with detailed specifications in the UI-SPEC.

The existing codebase provides strong foundations: DiagramStore already has `addSystem()` and `updateContent()`, DiagramRenderer renders reactively via `$derived`, the service layer has full CRUD including PATCH, and all required shadcn-svelte primitives (Tabs, Collapsible, Select) are installed except three new ones (Switch, ScrollArea, ToggleGroup) identified in the UI-SPEC.

**Primary recommendation:** Extend the existing DiagramStore with connection CRUD and auto-save `$effect`, build the sidebar as composable builder/ sub-components, and keep the DiagramRenderer untouched. The backend list endpoint needs a minor change to include `thumbnail_base64` (small ~5-15KB PNG strings, still excluding large `content` JSONB).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Left sidebar + right preview layout. Fixed-width sidebar (~360px) on the left, live DiagramRenderer preview fills remaining space on the right. Standard configurator pattern.
- **D-02:** Sidebar organized with shadcn Tabs component -- three tabs: Systems, Connections, Settings.
- **D-03:** Fixed-width sidebar (not resizable). Consistent with the control panel pattern in the existing MIRA codebase.
- **D-04:** Subtle inline save status indicator in the header bar -- small text/icon near the title showing "Saving...", "Saved", or a checkmark. Not toast-based for auto-save events.
- **D-05:** Category accordion with search bar at top. Expandable category sections show systems as clickable items with logos. Click to add system to the diagram. Component library's `category` and `display_order` drive the grouping and ordering.
- **D-06:** Already-added systems appear dimmed with a checkmark badge in the picker. Clicking them does nothing (prevents duplicates).
- **D-07:** Each system currently on the diagram has a remove button (small 'x' or remove action) in the Systems tab. Removal is sidebar-only -- no SVG preview interaction needed.
- **D-08:** "Add Custom System" button at the bottom of the Systems tab opens the existing `AddCustomSystemDialog` from Phase 2.
- **D-09:** Form-based connection creation, inline within the Connections tab. "Add Connection" button expands an inline form; connection list scrolls below. No dialog/modal.
- **D-10:** Connection form fields: source dropdown, target dropdown, direction toggle (unidirectional/bidirectional), integration type selector (native_connector, webhook_api, custom_build, api), label text input with suggestions.
- **D-11:** CONN-06 auto-suggest: When one end of the connection is m3ter and the other is a system with `is_native_connector = true`, the type selector auto-selects "Native Connector". SE can override.
- **D-12:** CONN-05 category-based label suggestions: Suggestion list derived from the source system's category (e.g., CRM systems suggest "Customer Data", "Usage Events"; Billing systems suggest "Invoice Data", "Payment Events"). SE can type a custom label.
- **D-13:** Connection list shows each connection with source->target names, type badge, label text, and Edit/Delete actions.
- **D-14:** Reactive `$effect` watches `currentDiagram.content` for changes, debounces 500ms, then calls `updateContent()`. Must skip initial load to avoid unnecessary save on page entry.
- **D-15:** Save status shown via inline indicator (D-04), not toasts. Toasts reserved for errors only.
- **D-16:** Client-side SVG-to-canvas snapshot. After auto-save, serialize the current SVG element to a small canvas, export as base64 PNG, include in the save payload as `thumbnail_base64`. All client-side, no server rendering.
- **D-17:** DiagramCard shows: thumbnail image at top (from `thumbnail_base64`), customer name, title (if different), last-edited relative timestamp (e.g., "2 hours ago"). Click navigates to the editor.
- **D-18:** PERS-03: Clicking a DiagramCard opens `/diagrams/[id]` editor route -- the existing route from Phase 2, now upgraded with the full builder UI.

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
- Settings tab content (likely background color toggle, show/hide labels -- from DiagramSettings type)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONN-01 | User can define connections between any two system nodes | ConnectionForm component with source/target Select dropdowns populated from current diagram systems; `addConnection()` store method creates DiagramConnection |
| CONN-02 | Each connection has a direction (unidirectional or bidirectional) | Switch component for direction toggle; DiagramConnection.direction field already typed as union |
| CONN-03 | Each connection has a text label describing the data flow | Label Input field in ConnectionForm; already rendered by ConnectionPill in Phase 2 renderer |
| CONN-05 | Tool suggests common data flows based on system types | Category-based suggestion map keyed by ComponentLibraryItem.category; dropdown below label input |
| CONN-06 | When connecting m3ter to a native connector system, auto-tag as "Native Connector" | Auto-detect logic using system role === 'hub' and ComponentLibraryItem.is_native_connector flag |
| PERS-02 | Diagram list view showing customer name, last edited date | Enhanced DiagramCard with relative timestamp via Intl.RelativeTimeFormat; backend list response needs `thumbnail_base64` field added |
| PERS-03 | User can load and continue editing a saved diagram | Already functional via `/diagrams/[id]` route; Phase 3 upgrades the layout to full builder |
| PERS-04 | Auto-save with debounced 500ms idle trigger | `$effect` in DiagramBuilder watching content snapshot; custom debounce utility; skip-first-run guard |
| PERS-05 | Thumbnail preview generated and displayed in diagram list view | SVG-to-canvas client-side: serialize SVG outerHTML, draw to 300x200 canvas, toDataURL PNG, include in save payload |
</phase_requirements>

## Standard Stack

### Core (already installed)

| Library | Version | Purpose | Verified |
|---------|---------|---------|----------|
| svelte | 5.53.5 | Component framework with runes | Verified via `npm ls` |
| @sveltejs/kit | 2.53.3 | Full-stack framework | Verified via `npm ls` |
| bits-ui | 2.16.2 | Headless primitives (underlying shadcn-svelte) | Verified via `npm ls` |
| lucide-svelte | 0.561+ | Icon set | Verified installed |
| tailwind-merge + clsx | Installed | `cn()` utility for class merging | Verified in `utils.ts` |

### shadcn-svelte Components to Install

| Component | Install Command | Purpose |
|-----------|----------------|---------|
| switch | `npx shadcn-svelte@latest add switch` | D-10: direction toggle (uni/bidirectional) |
| scroll-area | `npx shadcn-svelte@latest add scroll-area` | Sidebar scrolling for system picker and connection list |
| toggle-group | `npx shadcn-svelte@latest add toggle-group` | D-10: integration type selector (4 exclusive options) |

### No External Dependencies Needed

- **Debounce:** Custom 15-line utility function (no library needed for a single use case)
- **Relative time:** `Intl.RelativeTimeFormat` (built-in browser API, no library)
- **SVG-to-canvas:** Native browser APIs (SVG serialization + Canvas + Image)

## Architecture Patterns

### Recommended Component Structure
```
frontend/src/lib/components/diagram/
  builder/
    BuilderSidebar.svelte          # Tabs wrapper (Systems/Connections/Settings)
    SystemPicker.svelte            # Category accordion + search + system items
    SystemPickerItem.svelte        # Individual system row in picker
    ConnectionForm.svelte          # Inline connection create/edit form
    ConnectionList.svelte          # Scrollable list of existing connections
    ConnectionListItem.svelte      # Single connection with edit/delete
    SettingsPanel.svelte           # Background color + show labels toggle
    SaveStatusIndicator.svelte     # Inline save status (idle/saving/saved/error)
  DiagramBuilder.svelte            # Top-level layout: header + sidebar + preview
```

### Pattern 1: Store Extension (not new store)

**What:** Extend the existing `DiagramStore` class with new methods rather than creating a separate store.

**When to use:** When new functionality operates on the same `currentDiagram` state.

**Example:**
```typescript
// In diagrams.svelte.ts -- add to existing DiagramStore class
removeSystem(systemId: string) {
    if (!this.currentDiagram) return;
    this.currentDiagram = {
        ...this.currentDiagram,
        content: {
            ...this.currentDiagram.content,
            systems: this.currentDiagram.content.systems.filter(s => s.id !== systemId),
            // Also remove connections referencing this system
            connections: this.currentDiagram.content.connections.filter(
                c => c.source_id !== systemId && c.target_id !== systemId
            ),
        },
    };
}

addConnection(connection: DiagramConnection) {
    if (!this.currentDiagram) return;
    this.currentDiagram = {
        ...this.currentDiagram,
        content: {
            ...this.currentDiagram.content,
            connections: [...this.currentDiagram.content.connections, connection],
        },
    };
}
```

**Confidence:** HIGH -- follows the established pattern from Phase 2 where `addSystem()` was added.

### Pattern 2: Auto-Save $effect with Skip-First-Run

**What:** A reactive `$effect` that watches content changes, debounces, and persists. Must skip the initial load to avoid a save-on-mount.

**When to use:** D-14 auto-save requirement.

**Example:**
```typescript
// In DiagramBuilder.svelte
let isInitialLoad = $state(true);
let saveTimeoutId: ReturnType<typeof setTimeout> | null = null;

// Snapshot content for change detection
const contentSnapshot = $derived(
    diagramStore.currentDiagram
        ? JSON.stringify(diagramStore.currentDiagram.content)
        : null
);

$effect(() => {
    // Track the derived value to create dependency
    const _snapshot = contentSnapshot;

    if (isInitialLoad) {
        isInitialLoad = false;
        return;
    }

    if (saveTimeoutId) clearTimeout(saveTimeoutId);
    saveStatus = 'saving';

    saveTimeoutId = setTimeout(async () => {
        if (diagramStore.currentDiagram) {
            await diagramStore.updateContent(service, diagramStore.currentDiagram.content);
            if (!diagramStore.error) {
                saveStatus = 'saved';
                // Generate thumbnail after successful save
                await generateThumbnail();
            } else {
                saveStatus = 'error';
            }
        }
    }, 500);

    return () => {
        if (saveTimeoutId) clearTimeout(saveTimeoutId);
    };
});
```

**Confidence:** HIGH -- Svelte 5 `$effect` with cleanup is well-documented. The `JSON.stringify` snapshot approach is necessary because Svelte 5 `$derived` tracks deep object identity for change detection.

### Pattern 3: SVG-to-Canvas Thumbnail

**What:** Serialize the live SVG preview to a canvas, export as compressed PNG base64.

**When to use:** D-16 thumbnail generation after successful auto-save.

**Example:**
```typescript
async function generateThumbnail(): Promise<string | null> {
    const svgElement = document.querySelector('svg[role="img"]');
    if (!svgElement) return null;

    const svgData = new XMLSerializer().serializeToString(svgElement);
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = 300;
            canvas.height = 200;
            const ctx = canvas.getContext('2d')!;
            ctx.drawImage(img, 0, 0, 300, 200);
            URL.revokeObjectURL(url);
            resolve(canvas.toDataURL('image/png', 0.8));
        };
        img.onerror = () => {
            URL.revokeObjectURL(url);
            resolve(null);
        };
        img.src = url;
    });
}
```

**Confidence:** HIGH -- standard browser API approach. The SVG uses inline styles (Phase 2 decision REND-03), so no external stylesheet issues. No `foreignObject` in the SVG, so no cross-origin taint risk.

### Pattern 4: Category-Based Suggestions Map

**What:** Static map from component library categories to suggested connection labels.

**When to use:** D-12 label suggestions in ConnectionForm.

**Example:**
```typescript
const CATEGORY_SUGGESTIONS: Record<string, string[]> = {
    'CRM': ['Customer Data', 'Account Sync', 'Usage Events'],
    'Billing/Payments': ['Invoice Data', 'Payment Events', 'Subscription Status'],
    'Finance/ERP': ['Financial Data', 'Order Events', 'Revenue Recognition'],
    'Cloud Marketplace': ['Marketplace Listings', 'Usage Reports', 'Revenue Data'],
    'Analytics': ['Usage Analytics', 'Billing Reports', 'Revenue Data'],
    'Data Infrastructure': ['Raw Usage Data', 'Billing Records', 'Event Stream'],
    'Cloud Providers': ['Resource Usage', 'Compute Metrics', 'Storage Events'],
    'Monitoring': ['Usage Alerts', 'Billing Alerts', 'Threshold Events'],
    'Messaging': ['Billing Alerts', 'Usage Alerts', 'Notification Events'],
    'Developer Tools': ['API Events', 'Webhook Data', 'CI/CD Events'],
};
```

**Confidence:** HIGH -- categories verified from migration `015_component_library.sql` (10 categories: CRM, Billing/Payments, Finance/ERP, Cloud Marketplace, Analytics, Data Infrastructure, Cloud Providers, Monitoring, Messaging, Developer Tools).

### Pattern 5: Relative Time Formatting

**What:** Use `Intl.RelativeTimeFormat` for "2 hours ago" style timestamps.

**Example:**
```typescript
function formatRelativeTime(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

    if (diffSec < 60) return 'just now';
    if (diffMin < 60) return rtf.format(-diffMin, 'minute');
    if (diffHour < 24) return rtf.format(-diffHour, 'hour');
    return rtf.format(-diffDay, 'day');
}
```

**Confidence:** HIGH -- `Intl.RelativeTimeFormat` is supported in all modern browsers (98%+ coverage). No library needed.

### Anti-Patterns to Avoid

- **Creating a separate BuilderStore:** The DiagramStore already owns `currentDiagram`. Adding a second store creates sync issues. Extend the existing store instead.
- **Using `$effect` without skip-first-run:** An auto-save `$effect` fires immediately on mount, causing an unnecessary API call on page load.
- **Debounce inside the store:** The debounce timer is UI concern (component-level), not store concern. Keep it in DiagramBuilder.svelte.
- **Toast for every auto-save:** D-15 explicitly prohibits this. Use inline SaveStatusIndicator only.
- **Direct SVG DOM mutation:** The renderer is driven by `content` prop via `$derived`. Never modify the SVG DOM directly -- always update `currentDiagram.content` via store methods.
- **Using canvas `toDataURL` with external images:** The SVG renderer uses `data:` URIs for logos (Phase 2 logo proxy converts to base64), so no cross-origin taint. But if any `http://` URLs leak in, canvas export silently fails.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tabs | Custom tab switcher | shadcn-svelte Tabs (bits-ui) | ARIA roles, keyboard nav, animation built-in |
| Accordion/collapsible | Custom expand/collapse | shadcn-svelte Collapsible (bits-ui) | `aria-expanded`, animation, accessible |
| Select dropdowns | Custom dropdown | shadcn-svelte Select (bits-ui) | Portal rendering, keyboard nav, scroll buttons |
| Direction toggle | Custom checkbox wrapper | shadcn-svelte Switch (bits-ui) | `role="switch"`, `aria-checked`, animation |
| Type selector | Custom radio group | shadcn-svelte ToggleGroup (bits-ui) | `role="group"`, `aria-pressed`, exclusive selection |
| Scrollable containers | CSS `overflow-y: auto` alone | shadcn-svelte ScrollArea | Custom scrollbar styling, consistent cross-browser |

**Key insight:** All UI primitives are available through the shadcn-svelte/bits-ui stack already in the project. No third-party UI libraries needed.

## Common Pitfalls

### Pitfall 1: Auto-Save Fires on Initial Load
**What goes wrong:** The `$effect` watching `currentDiagram.content` fires immediately when the page loads and the store is populated, triggering an unnecessary save.
**Why it happens:** Svelte 5 `$effect` runs once on mount with current values.
**How to avoid:** Use a `isInitialLoad` flag that gets set to `false` after the first `$effect` run. The effect returns early when the flag is true.
**Warning signs:** Network tab shows a PATCH request immediately on page load.

### Pitfall 2: Thumbnail Canvas Taint from External URLs
**What goes wrong:** `canvas.toDataURL()` throws a SecurityError if the SVG references external image URLs.
**Why it happens:** Cross-origin images taint the canvas.
**How to avoid:** Phase 2 already converts all logos to base64 via the logo proxy (COMP-06). Verify that `logo_base64` fields contain `data:` URIs or `monogram:` strings, never `http://` URLs. The DiagramRenderer SVG uses only inline styles (REND-03).
**Warning signs:** `toDataURL()` returns empty string or throws DOMException.

### Pitfall 3: Stale Content in Debounced Save
**What goes wrong:** The debounce callback captures a stale reference to `currentDiagram.content` from when the timeout was set, not when it fires.
**Why it happens:** JavaScript closure captures the value at setTimeout creation time.
**How to avoid:** Read `diagramStore.currentDiagram.content` inside the setTimeout callback, not in the outer scope. The store is a module-level singleton, so reading it at execution time gets the latest value.
**Warning signs:** Saved content is missing the most recent change.

### Pitfall 4: System Removal Orphans Connections
**What goes wrong:** Removing a system from the diagram leaves dangling connections that reference the deleted system ID.
**Why it happens:** The `removeSystem()` method only filters the systems array.
**How to avoid:** `removeSystem()` must also filter connections where `source_id` or `target_id` matches the removed system ID. This is a single atomic operation on the content object.
**Warning signs:** Renderer throws errors for connections with missing node positions.

### Pitfall 5: DiagramListItem Missing Thumbnail
**What goes wrong:** The diagram list page cannot show thumbnails because `DiagramListItem` type and backend `DiagramListResponse` exclude `thumbnail_base64`.
**Why it happens:** Phase 1 deliberately excluded it for list performance.
**How to avoid:** Add `thumbnail_base64` to the backend `DiagramListResponse` schema and the `LIST_SELECT_FIELDS` constant. Also update the frontend `DiagramListItem` type. Thumbnail PNGs at 300x200 compressed are ~5-15KB, much smaller than the excluded `content` JSONB.
**Warning signs:** Thumbnails are saved but never displayed in the list.

### Pitfall 6: Select Dropdown Value Type Mismatch
**What goes wrong:** shadcn-svelte Select `value` is typed as `string` but DiagramSystem `id` is also `string`, so this works. However, the `onValueChange` callback pattern differs from bits-ui 1.x.
**Why it happens:** bits-ui 2.x uses `$bindable(value)` pattern, not event callbacks.
**How to avoid:** Use `bind:value` on Select.Root, not `onValueChange`. The installed shadcn-svelte Select component (verified in source) uses `value = $bindable()`.
**Warning signs:** Select value doesn't update, or updates are one step behind.

### Pitfall 7: JSON.stringify Comparison Performance
**What goes wrong:** `JSON.stringify` on every content change for the auto-save `$effect` dependency tracking could be expensive with many systems/connections.
**Why it happens:** Deep comparison via serialization on reactive updates.
**How to avoid:** For a typical diagram (5-20 systems, 5-30 connections), the stringify is sub-millisecond. This is not a concern for v1 scale. If it becomes an issue, switch to a shallow version counter incremented on each mutation.
**Warning signs:** UI jank when typing quickly in settings fields.

## Backend Change Required

### Add `thumbnail_base64` to List Response

**File:** `backend/app/schemas/diagrams.py`

Add `thumbnail_base64: str | None = None` to `DiagramListResponse`.

**File:** `backend/app/services/diagram_service.py`

Update `LIST_SELECT_FIELDS` to include `thumbnail_base64`:
```python
LIST_SELECT_FIELDS = (
    "id,user_id,customer_name,title,project_id,schema_version,"
    "thumbnail_base64,created_at,updated_at"
)
```

**File:** `frontend/src/lib/types/diagram.ts`

Add `thumbnail_base64: string | null;` to `DiagramListItem`.

**File:** `backend/tests/test_api_diagrams.py`

Update the list response test to expect (not exclude) `thumbnail_base64`.

**Confidence:** HIGH -- the thumbnail PNG at 300x200 is ~5-15KB base64, while the excluded `content` JSONB can be 50-200KB. Including thumbnail in list is a reasonable tradeoff.

## Code Examples

### shadcn-svelte Tabs Usage (verified from installed source)
```svelte
<script lang="ts">
    import * as Tabs from '$lib/components/ui/tabs';
</script>

<Tabs.Root value="systems">
    <Tabs.List>
        <Tabs.Trigger value="systems">Systems</Tabs.Trigger>
        <Tabs.Trigger value="connections">Connections</Tabs.Trigger>
        <Tabs.Trigger value="settings">Settings</Tabs.Trigger>
    </Tabs.List>
    <Tabs.Content value="systems">
        <!-- SystemPicker -->
    </Tabs.Content>
    <Tabs.Content value="connections">
        <!-- ConnectionForm + ConnectionList -->
    </Tabs.Content>
    <Tabs.Content value="settings">
        <!-- SettingsPanel -->
    </Tabs.Content>
</Tabs.Root>
```
Source: Verified from `frontend/src/lib/components/ui/tabs/tabs.svelte` -- uses `value = $bindable('')`.

### shadcn-svelte Collapsible Usage (verified from installed source)
```svelte
<script lang="ts">
    import * as Collapsible from '$lib/components/ui/collapsible';
</script>

<Collapsible.Root open={true}>
    <Collapsible.Trigger>
        Category Name
    </Collapsible.Trigger>
    <Collapsible.Content>
        <!-- System items -->
    </Collapsible.Content>
</Collapsible.Root>
```
Source: Verified from `frontend/src/lib/components/ui/collapsible/collapsible.svelte` -- uses `open = $bindable(false)`.

### shadcn-svelte Select Usage (verified from installed source)
```svelte
<script lang="ts">
    import * as Select from '$lib/components/ui/select';
    let sourceId = $state<string>('');
</script>

<Select.Root type="single" bind:value={sourceId}>
    <Select.Trigger>
        <span>{selectedName || 'Select source'}</span>
    </Select.Trigger>
    <Select.Content>
        {#each systems as system (system.id)}
            <Select.Item value={system.id}>{system.name}</Select.Item>
        {/each}
    </Select.Content>
</Select.Root>
```
Source: Verified from `frontend/src/lib/components/ui/select/select.svelte` -- uses `value = $bindable()`.

### DiagramStore addSystem Pattern (existing -- extend this pattern)
```typescript
// Source: frontend/src/lib/stores/diagrams.svelte.ts (existing code)
addSystem(system: DiagramSystem) {
    if (!this.currentDiagram) return;
    this.currentDiagram = {
        ...this.currentDiagram,
        content: {
            ...this.currentDiagram.content,
            systems: [...this.currentDiagram.content.systems, system],
        },
    };
}
```

### Debounce Utility (custom -- no library needed)
```typescript
// In $lib/utils.ts or inline in DiagramBuilder
function debounce<T extends (...args: any[]) => any>(
    fn: T,
    delay: number
): (...args: Parameters<T>) => void {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    return (...args: Parameters<T>) => {
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
}
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.0 with jsdom environment |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test -- --run` |
| Full suite command | `cd frontend && npm run test -- --run` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONN-01 | addConnection() and removeConnection() store methods | unit | `cd frontend && npx vitest run src/lib/stores/diagrams.svelte.test.ts` | Exists (extend) |
| CONN-02 | Connection direction field in store methods | unit | Same as CONN-01 | Exists (extend) |
| CONN-03 | Connection label field in store methods | unit | Same as CONN-01 | Exists (extend) |
| CONN-05 | Category suggestion map returns correct labels | unit | `cd frontend && npx vitest run src/lib/components/diagram/builder/ConnectionForm.svelte.test.ts` | Wave 0 |
| CONN-06 | Native connector auto-detect logic | unit | Same as CONN-05 | Wave 0 |
| PERS-02 | Relative time formatter | unit | `cd frontend && npx vitest run src/lib/utils.test.ts` | Wave 0 (new test file or extend) |
| PERS-03 | Load diagram into editor | unit | Covered by existing `loadDiagram` test | Exists |
| PERS-04 | Debounce utility function | unit | `cd frontend && npx vitest run src/lib/utils.test.ts` | Wave 0 |
| PERS-04 | removeSystem cascades connection removal | unit | `cd frontend && npx vitest run src/lib/stores/diagrams.svelte.test.ts` | Exists (extend) |
| PERS-05 | Thumbnail generation (SVG-to-canvas) | manual-only | Cannot test in jsdom (no Canvas rendering) | N/A |
| Backend | DiagramListResponse includes thumbnail_base64 | unit | `cd backend && pytest tests/test_api_diagrams.py -x` | Exists (modify) |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run test -- --run`
- **Per wave merge:** Full frontend + backend test suite
- **Phase gate:** All tests green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/src/lib/components/diagram/builder/ConnectionForm.svelte.test.ts` -- covers CONN-05, CONN-06 (suggestion map and auto-detect logic)
- [ ] `frontend/src/lib/utils.test.ts` or extend existing -- covers PERS-02 (relative time), PERS-04 (debounce)
- [ ] Extend `frontend/src/lib/stores/diagrams.svelte.test.ts` -- covers CONN-01, CONN-02, CONN-03 (new store methods)
- [ ] Update `backend/tests/test_api_diagrams.py` -- thumbnail_base64 now in list response

## Open Questions

1. **Thumbnail base64 size in list responses**
   - What we know: 300x200 PNG at quality 0.8 is typically 5-15KB base64 encoded. The list endpoint currently excludes it.
   - What's unclear: With 50+ diagrams in a list, this adds 250KB-750KB to the list response. Acceptable for v1.
   - Recommendation: Proceed with adding thumbnail_base64 to list response. If performance becomes an issue in v2, consider storing thumbnails in Supabase Storage and returning URLs instead.

2. **SVG serialization fidelity for thumbnails**
   - What we know: `XMLSerializer().serializeToString()` captures the SVG as-is including inline styles. All styles are inline per REND-03.
   - What's unclear: Whether all `data:` URI logos render correctly at 300x200 canvas resolution.
   - Recommendation: Test with a real diagram containing logos. If logos don't render, fall back to rendering without logos (still useful as a visual identifier).

## Sources

### Primary (HIGH confidence)
- `frontend/src/lib/stores/diagrams.svelte.ts` -- Existing store, verified methods and patterns
- `frontend/src/lib/types/diagram.ts` -- All type definitions verified
- `frontend/src/lib/components/ui/tabs/tabs.svelte` -- Tabs API verified (bits-ui 2.16.2)
- `frontend/src/lib/components/ui/select/select.svelte` -- Select API verified
- `frontend/src/lib/components/ui/collapsible/collapsible.svelte` -- Collapsible API verified
- `backend/migrations/015_component_library.sql` -- 10 categories verified for suggestion map
- `backend/app/schemas/diagrams.py` -- DiagramUpdate supports `thumbnail_base64`
- `backend/app/services/diagram_service.py` -- LIST_SELECT_FIELDS verified, PATCH endpoint verified
- `.planning/phases/03-configurator-ui/03-UI-SPEC.md` -- Full design contract verified
- `.planning/phases/03-configurator-ui/03-CONTEXT.md` -- All 18 decisions verified

### Secondary (MEDIUM confidence)
- SVG-to-canvas approach: Standard browser API, widely documented. Canvas taint risk mitigated by Phase 2's base64 logo approach.
- `Intl.RelativeTimeFormat`: Browser API with 98%+ support per Can I Use.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified from installed `node_modules` and existing code
- Architecture: HIGH -- extends established patterns from Phase 2, all component APIs verified from source
- Pitfalls: HIGH -- identified from code review of existing store, service, and renderer implementations
- Backend change: HIGH -- minimal change (add one field to list response), existing PATCH already supports `thumbnail_base64`

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable -- all dependencies are installed and versioned)
