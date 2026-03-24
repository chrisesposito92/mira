---
phase: 2
reviewers: [gemini, codex]
reviewed_at: 2026-03-24T10:15:00Z
plans_reviewed: [02-01-PLAN.md, 02-02-PLAN.md, 02-03-PLAN.md, 02-04-PLAN.md, 02-05-PLAN.md]
---

# Cross-AI Plan Review -- Phase 2: Rendering Engine

## Gemini Review

This review covers the **Phase 2: Rendering Engine** implementation plans (02-01 through 02-05) for the m3ter Integration Architecture Diagrammer.

### 1. Summary
The proposed plans are architecturally sound and demonstrate a deep understanding of the specific constraints of SVG rendering for high-fidelity export. The separation of concerns between the pure-logic layout engine (02-01), the reactive state management (02-02), and the atomic SVG components (02-03, 02-04) is excellent. The use of Svelte 5 runes (`$state`, `$derived`) and the strict adherence to inline styles ensure both developer productivity and the technical requirement for "clean" SVG exports. The inclusion of TDD for the layout math and store logic provides high confidence in the core engine's stability.

### 2. Strengths
* **Export-First Design:** The commitment to inline hex styles and zero `foreignObject` usage is the correct choice for ensuring cross-platform SVG/PNG export compatibility in Phase 4.
* **Marker Optimization:** Using `context-stroke` for SVG markers is a sophisticated way to handle multi-colored connections without inflating the DOM with duplicate `<marker>` definitions for every color.
* **Reactive Orchestration:** Using `$derived(layoutDiagram(...))` in the top-level renderer ensures the UI remains perfectly in sync with data changes (REND-01) without manual event plumbing.
* **Robust Layout Logic:** The zone-based approach with sin/cos math is more predictable and easier to debug than a force-directed layout, which aligns with the "configurator" vs "WYSIWYG" project philosophy.
* **Monogram Fallback:** The regex-based monogram parser (`monogram:INIT:COLOR`) provides an elegant solution for systems without logos, maintaining the "branded" feel regardless of data completeness.

### 3. Concerns

* **SVG Text Wrapping (MEDIUM):**
    * **Issue:** Standard SVG `<text>` elements do not support automatic line wrapping. If a system name or a connection pill label is long, it will overflow its container (Card or Pill).
    * **Impact:** Broken layout for systems with long names (e.g., "Enterprise Resource Planning Connector").

* **Node Collision & Sizing (MEDIUM):**
    * **Issue:** Plan 02-01 mentions fixed hub/prospect coordinates and zone centers. However, `GroupCard` components grow based on the number of logos they contain (D-07).
    * **Impact:** Large group cards in adjacent zones might overlap if the layout algorithm only considers center-points and not the bounding box (BBox) of the cards.

* **Logo Export Compatibility (LOW):**
    * **Issue:** Using a backend proxy for logos is great for the live preview, but standard SVG-to-PNG export tools often struggle with external URLs or requires CORS-enabled `<img>` tags.
    * **Impact:** Phase 4 might require refactoring these to Base64 data URIs.

* **Z-Index of Connection Pills (LOW):**
    * **Issue:** Plan 02-05 states "Connections rendered first (behind nodes)". While lines should be behind nodes, if a connection crosses *behind* another node, the **Pill Label** might be obscured.
    * **Impact:** Partially unreadable data flow labels.

### 4. Suggestions

* **Text Truncation Utility:** In `diagram-layout.ts`, add a helper function to truncate strings based on an estimated character width (e.g., `truncateText(str, maxLength)`). Apply this to `SystemCard` and `ConnectionPill` to prevent layout breaking.
* **Dynamic Zone Buffering:** Update the layout algorithm in 02-01 to accept an optional `nodeSize` map. If a node is a `GroupCard` with > 4 logos, the algorithm should push the zone center further out from the hub to prevent overlap.
* **Separate Connection Layering:** In `DiagramRenderer.svelte`, consider splitting the connection rendering into two passes:
    1. Render all **Lines** (bottom layer).
    2. Render all **Nodes** (middle layer).
    3. Render all **Connection Pills** (top layer).
    * This ensures that data flow labels are never hidden behind cards.
* **SVG Filter IDs:** Ensure `SvgDefs.svelte` uses unique IDs for filters (e.g., `filter-shadow-{diagramId}`) if multiple diagrams might ever be rendered on the same page, though a singleton editor makes this less risky.

### 5. Risk Assessment
**Risk Level: LOW**

The plans are highly detailed and follow Svelte 5 best practices. The "non-autonomous" gate in Plan 02-05 is a smart safety measure for visual-heavy work. The primary risks are aesthetic (text overflow, card overlapping), which are easily tunable within the `constants.ts` and `diagram-layout.ts` files provided the logic is properly encapsulated as planned. The technical path to SVG export is well-protected by the "No Tailwind" constraint.

---

## Codex Review

**Overall**
Grounded against the current repo, the phase is split sensibly, but 3 blockers recur across the plans: there is no explicit prospect-node model in the current schema, the editor route is not reachable from the existing list UI, and Plan 05 relies on a wrong logo endpoint plus a non-serializable service object. Until those are fixed, the phase can render a demo but not a stable end-to-end editor.

### Plan 02-01
**Summary**
Good foundation. A pure layout function plus centralized SVG constants is the right first move, but the plan is building on an ambiguous data model, especially around the prospect node and future connection targeting.

**Strengths**
- Pure-function layout is the right place to start TDD.
- Constants are centralized instead of leaking hex values and dimensions into components.
- The test list covers determinism, empty-state behavior, monogram parsing, and high-count reflow.

**Concerns**
- `HIGH`: Prospect detection is heuristic-based even though the current schema has no explicit prospect field in `diagram.ts` or `diagrams.py`. Plan 01's null/null/name-match logic will collide with custom systems added later.
- `MEDIUM`: The current schema still stores `x`/`y` on every system, but the plan never states whether auto-layout ignores or rewrites them. That will create confusion in later phases.
- `MEDIUM`: Tests check bounds, not collision quality. There is no explicit coverage for >5 categories wrapping, large grouped cards, long names, or overlap between grouped and standalone nodes.

**Suggestions**
- Add explicit node identity now: reserved `kind`/`role` for `prospect` and `hub`, or a dedicated `prospect_name` field.
- Extend `LayoutResult` with a `nodesById` map or anchor metadata so later connection rendering is not forced to re-scan and guess.
- Add overlap tests for wrapped zones, mixed grouped/standalone layouts, and long labels.

**Risk Assessment:** `MEDIUM-HIGH`

### Plan 02-02
**Summary**
Extending the existing singleton store is the right pattern for this repo, but the state lifecycle is still loose and the plan does not fully reconcile list-state methods with editor-state methods.

**Strengths**
- Reuses the established class-based Svelte 5 store pattern.
- Includes store-level tests for fetch, save, and clear flows.
- Keeps component-library state close to diagram-editing state.

**Concerns**
- `HIGH`: The plan says to preserve existing methods unchanged, but current `clear()` only resets list state. After adding `currentDiagram`, `componentLibrary`, and `saving`, stale editor state can survive unless `clear()` is expanded.
- `MEDIUM`: `loadComponentLibrary()` has no loading state and weak failure semantics, so stale component data can remain silently.
- `MEDIUM`: `addSystem()` mutates local state only, while persistence is deferred elsewhere. That is workable, but it creates room for UI/server drift.

**Suggestions**
- Make `clear()` call `clearEditor()` or reset all store fields consistently.
- Return `{ ok, error }` from the new editor methods, like the object store does.
- Prefer a single persistence path such as `updateContent()`/`persistCurrentDiagram()` rather than local mutation plus ad hoc save calls elsewhere.

**Risk Assessment:** `MEDIUM`

### Plan 02-03
**Summary**
The component split is good, and the SVG-only discipline is correct, but the grouped-card design currently misses the actual grouped-logo requirement and the tests are too shallow for a visually sensitive phase.

**Strengths**
- Good separation of `SvgDefs`, node primitives, and monogram rendering.
- Inline-style-only SVG is enforced explicitly.
- Hub/prospect componentization matches the rendering model well.

**Concerns**
- `HIGH`: `GroupCard` is specified to render full `SystemCard` children, but the spec calls for a logo grid inside a containing card, not nested standalone cards. That is likely a visual miss on REND-05.
- `MEDIUM`: The tests only verify text and one fill color. They do not verify grid layout, multi-logo rows, monogram fallback inside groups, or no-overflow behavior.
- `MEDIUM`: Long system/category names are not accounted for, which is a common SVG failure mode.

**Suggestions**
- Split grouped content into a compact `GroupItem`/logo-grid renderer instead of reusing the full `SystemCard`.
- Add tests for 2-column or 3-column grid placement, mixed real-logo/monogram rendering, and long-name clipping/truncation.
- Treat grouped cards as a distinct visual language, not "cards inside cards."

**Risk Assessment:** `MEDIUM-HIGH`

### Plan 02-04
**Summary**
Connection rendering is isolated cleanly, but the current spec is still under-defined around anchors, missing-node handling, and label visibility.

**Strengths**
- Good separation between line and pill.
- Color mapping is explicit and tied to the requirement.
- Directionality tests cover the main marker cases.

**Concerns**
- `MEDIUM-HIGH`: The plan draws center-to-center lines, which will run markers through cards/hub rather than terminating on edges. That will look unpolished.
- `MEDIUM`: Missing-node behavior is unspecified. One stale connection could break or distort the renderer.
- `MEDIUM`: `show_labels` is unresolved in the plan itself: "passed via additional prop or always shown". That is incomplete.

**Suggestions**
- Add edge-anchor calculation or anchor metadata to the layout result.
- Skip invalid connections safely instead of assuming all IDs resolve.
- Pass `showLabels` explicitly from the renderer and test both branches.

**Risk Assessment:** `MEDIUM`

### Plan 02-05
**Summary**
This is the highest-risk plan. It connects the right pieces, but several key integration details are wrong against the current repo, and those issues will block the editor flow even if the individual components are implemented correctly.

**Strengths**
- Good final orchestration target.
- Correct paint order: connections first, nodes after.
- Human visual verification is appropriate for this phase.

**Concerns**
- `HIGH`: The plan returns `diagramService` from universal `+page.ts`. That should not be part of route data.
- `HIGH`: The dialog fetches `/api/logo-proxy`, but the actual authenticated route is `/api/logos/proxy` (router prefix `/api/logos`, endpoint `/proxy`). The same wrong path appears in CONTEXT.md and UI-SPEC.
- `HIGH`: The current diagrams list UI does not navigate to `[id]`; `DiagramCard.svelte` has no link/click path except delete. The plan assumes a reachable editor but does not include the files needed to reach it.
- `HIGH`: The navy background is only CSS on `<svg>`. For SVG export, that is unreliable; it should be an actual background `<rect>`.
- `MEDIUM-HIGH`: `handleAddSystem()` applies an optimistic local mutation and only toasts on PATCH failure. That leaves UI and persisted state out of sync.
- `MEDIUM`: Plan 05 bypasses the store methods added in Plan 02 and creates a second persistence path.
- `MEDIUM`: COMP-04 is still only partially addressed because the underlying schema still has no explicit editable prospect field.

**Suggestions**
- Build the service/client in the page component; do not return it from `load`.
- Add actual navigation to the editor from the list page/card, or redirect to the new editor immediately after create.
- Use the real `/api/logos/proxy` endpoint through `ApiClient`, not raw fetch to a guessed URL.
- Render a full-canvas `<rect fill={CANVAS_BG}>` as the first SVG child.
- Route persistence through `diagramStore.updateContent()` and roll back optimistic edits on save failure.
- If COMP-04 is truly in-scope, add prospect metadata to the schema before execution.

**Risk Assessment:** `HIGH`

---

## Consensus Summary

### Agreed Strengths
*(Mentioned by both reviewers)*

1. **Separation of concerns is excellent** -- pure layout function, reactive store, atomic SVG components, and integration orchestrator are properly isolated
2. **Export-first SVG discipline** -- inline styles only, no Tailwind on SVG, no foreignObject -- both reviewers agree this is the right approach for Phase 4 compatibility
3. **TDD for the layout algorithm** -- pure function with comprehensive tests gives high confidence in the computational core
4. **context-stroke for marker inheritance** -- avoids marker duplication, keeps SVG defs clean
5. **Wave dependency structure** -- Plan 01+02 in parallel (Wave 1), 03+04 in parallel (Wave 2), 05 integrates all (Wave 3) is well-ordered

### Agreed Concerns
*(Raised by both reviewers -- highest priority for plan revision)*

1. **HIGH: SVG text overflow / long names** -- Both flagged that SVG `<text>` does not wrap. Long system names and connection labels will overflow their containers. Need truncation or ellipsis utility.
2. **HIGH: Node collision / overlap** -- Layout algorithm considers zone centers but not bounding boxes. Large group cards in adjacent zones will overlap. Need dynamic zone buffering based on actual card dimensions.
3. **HIGH: Connection lines run through nodes** -- Center-to-center lines will draw markers inside cards/hub. Need edge-anchor calculation to terminate lines at card boundaries.
4. **HIGH: Logo endpoint path is wrong** -- Plans reference `/api/logo-proxy` but the actual route is `/api/logos/proxy`. Must be corrected in CONTEXT.md, UI-SPEC, and Plan 05.
5. **MEDIUM-HIGH: GroupCard visual design** -- Codex flagged nested SystemCards inside GroupCard may not match the spec's "logo grid" visual. Gemini flagged the BBox growth concern. Both point to GroupCard needing more careful design.
6. **MEDIUM: Stale state / persistence path** -- Both note that `addSystem()` is local-only, creating UI/server drift risk. Plan 05 bypasses the store's `updateContent()`.

### Divergent Views
*(Where reviewers disagreed -- worth investigating)*

1. **Overall risk assessment**: Gemini rates the phase LOW risk (aesthetic issues are tunable), while Codex rates Plan 05 HIGH risk (integration mismatches against the actual repo). **Resolution: Codex's concerns are verified -- the logo endpoint IS wrong, DiagramCard HAS no navigation link, and `diagramService` being returned from `load` IS a SvelteKit anti-pattern. Codex's higher risk rating for Plan 05 is more accurate.**
2. **Prospect node data model**: Codex flags the lack of an explicit `kind`/`role` field as HIGH risk for prospect detection colliding with custom nodes. Gemini doesn't mention this. **Resolution: Worth addressing -- heuristic detection is fragile.**
3. **SVG background method**: Codex specifically flags that `style="background: ..."` on `<svg>` won't export correctly and needs a `<rect>`. Gemini doesn't mention this. **Resolution: Codex is correct -- Phase 4 export needs an actual SVG `<rect>` for the background, not CSS.**
4. **DiagramCard navigation gap**: Codex flags this as a HIGH blocker (editor unreachable from list page). Gemini doesn't check repo state. **Resolution: Confirmed -- DiagramCard has no click-through to `[id]`. Plan 05 must add this.**

### Action Items for Plan Revision

| Priority | Issue | Plans Affected | Fix |
|----------|-------|----------------|-----|
| HIGH | Logo endpoint path wrong (`/api/logo-proxy` -> `/api/logos/proxy`) | 05, CONTEXT, UI-SPEC | Correct all references |
| HIGH | DiagramCard has no navigation to editor route | 05 | Add click-through link or wrap card in anchor |
| HIGH | SVG background needs `<rect>`, not CSS `background:` | 05 | Add `<rect>` as first SVG child in DiagramRenderer |
| HIGH | `diagramService` returned from `+page.ts` load | 05 | Build service in component, not route data |
| HIGH | Prospect node detection is heuristic-fragile | 01, 05 | Add explicit `role` field to DiagramSystem or dedicated prospect_name to DiagramContent |
| MEDIUM-HIGH | Center-to-center lines run through nodes | 04 | Add edge-anchor calculation |
| MEDIUM-HIGH | GroupCard renders nested SystemCards (should be compact logo grid) | 03 | Create compact GroupItem renderer |
| MEDIUM | Long text overflow in SVG | 01, 03, 04 | Add truncation utility |
| MEDIUM | Node collision from large group cards | 01 | Add BBox-aware zone buffering |
| MEDIUM | `clear()` doesn't reset editor state | 02 | Make `clear()` call `clearEditor()` |
| MEDIUM | `show_labels` prop unresolved in Plan 04 | 04 | Pass explicitly from renderer |
| LOW | Connection pills may be hidden behind nodes | 05 | Three-layer rendering (lines, nodes, pills) |
