---
phase: 4
reviewers: [gemini, codex]
reviewed_at: 2026-03-25T00:00:00Z
plans_reviewed: [04-01-PLAN.md, 04-02-PLAN.md]
---

# Cross-AI Plan Review — Phase 4

## Gemini Review

This review evaluates the implementation plans for **Phase 4: Export Pipeline**. The plans demonstrate a high level of technical maturity, specifically addressing the "hidden" complexities of SVG serialization and Canvas rendering that often plague web-based export tools.

---

### 1. Summary
The proposed plans provide a robust, modular approach to diagram exporting. **Plan 04-01** is exceptionally well-researched, proactively solving common pitfalls like Unicode errors, marker rendering, and font-weight mismatches. **Plan 04-02** correctly follows established UI patterns within the project while ensuring the user experience is "guarded" via empty-state tooltips. The decision to override the previous "400-weight only" font decision in favor of a variable font is a critical correction that ensures visual fidelity.

---

### 2. Strengths
*   **Pitfall Awareness:** The utility module directly implements solutions for `btoa` stack overflows, Unicode characters, and SVG marker "context-stroke" failures—issues that are often only discovered late in QA.
*   **Testability:** By structuring the engine as a standalone utility with 18 behavior specs, the team can verify the complex XML/String manipulation logic without mounting Svelte components.
*   **Font Fidelity:** Shifting to the Inter Variable font (~160KB) is the correct architectural choice. Since the diagrams utilize weights 500-700 for headers and labels, a single-weight font would have resulted in "faux-bolding" or thin text in the export.
*   **Canvas Safety:** Using Data URLs for the PNG conversion process avoids the `createObjectURL` revocation lifecycle issues and ensures the canvas remains "clean" for the final export.

---

### 3. Concerns

*   **Logo Inlining Logic (MEDIUM):**
    Requirement **EXPO-03** mandates pre-fetching logos to Data URLs. While the "Research Findings" mention this, **Plan 04-01** does not explicitly detail the mechanism for traversing the SVG DOM to find `<image>` tags and replacing their `href` with base64 data. If this isn't handled within the utility, the PNG export will likely fail (blank squares) due to the "tainted canvas" security model when the SVG contains external proxy URLs.
*   **Asynchronous Font Loading (LOW):**
    The plan mentions lazy-loading the font on the first export. Since the font is an asset in `src/lib/assets`, the code must `fetch()` the file and convert it to base64 at runtime. This introduces an async gap between the user clicking "Export" and the file downloading.
*   **SVG "context-stroke" Markers (MEDIUM):**
    The fix for markers involves rewriting the SVG string to create per-color marker definitions. This is a complex string-manipulation task. If the diagram has many connections, the resulting SVG string could grow significantly.

---

### 4. Suggestions

*   **Explicit Logo Pre-processor:** Add a step in `exportDiagram` that identifies all `<image>` elements, fetches their current `src` (likely the logo proxy), and converts them to base64 *before* the SVG is serialized to the final string.
*   **Add "Processing" Feedback:** Although Decision **D-02** requests "no spinner," the combination of font-fetching (160KB) and logo-fetching/base64-encoding could take 500ms–1s on slower connections. I recommend adding a transient `exporting` state to the button (e.g., changing the icon to a small spinner or disabling the button) to prevent double-clicks during the async processing.
*   **Font Asset Format:** Ensure the Inter variable font is provided in `.woff2` for the web UI, but verify that the `xmlserializer` + `canvas` pipeline in the target browsers correctly renders `.woff2` when embedded in a CSS `@font-face` block inside an SVG. (Usually works, but some older Chromium versions prefer `.ttf` for base64 inlining in this specific edge case).
*   **Filename Sanitization:** In `generateFilename`, ensure that characters like `/`, `\`, and `:` are explicitly stripped even after slugifying to prevent OS-level file saving errors.

---

### 5. Risk Assessment: LOW
The risk is low because the heavy lifting (the Export Utility) is being built first and is isolated for testing.

**Justification:**
The team has already identified the most difficult technical hurdles (Canvas tainting and SVG marker rendering). The only remaining risk is the coordination of the asynchronous fetching of logos and fonts before the synchronous Canvas `drawImage` call occurs. If the logo-inlining is implemented as suggested, the phase should be highly successful.

**Verdict:** Proceed with Wave 1, ensuring the logo-inlining logic is explicitly added to the `exportDiagram` implementation.

---

## Codex Review

Overall, the phase split is sound. `04-01` carries most of the real risk and is pointed at the right problems; `04-02` is appropriately thin, but it leaves a few interaction details under-specified enough that they could slip through without tests.

## Plan 04-01: Export Utility Module

**Summary**

This is the right place to concentrate the hard work. The plan maps well to the current renderer, which already has the exact export hazards you called out: `context-stroke` markers in SvgDefs.svelte, mixed font weights in SystemCard, ProspectNode, HubNode, and GroupCard, plus an existing blob-URL thumbnail path in DiagramBuilder.svelte. The main weakness is that the plan still sounds too string-surgery-heavy for something that is fundamentally DOM/SVG-structure-sensitive.

**Strengths**

- Directly addresses the real technical risks in the current renderer rather than adding generic export code.
- Correctly overturns D-05: the live SVG already uses 500/600/700 weights, so 400-only would not meet EXPO-04.
- Utility-first split is good; this logic should stay outside the Svelte component.
- Data URL for PNG is the right safety choice given the canvas taint concern.
- Font caching is sensible for repeat exports.
- Filename helpers and base64 helpers are worth isolating and testing.

**Concerns**

- **HIGH:** The function list does not include a UTF-8-safe SVG-to-data-URL helper. Research calls out Unicode `btoa()` failure, and customer names / labels are user text. If this is omitted, PNG export will fail on non-ASCII diagrams.
- **HIGH:** `injectFont`, `fixContextStroke`, and `ensureSvgDimensions` sound like raw string transforms. That is brittle against SVG structure changes, whitespace, extra `<defs>`, or future renderer changes. Parse/manipulate the SVG DOM instead.
- **MEDIUM:** `exportDiagram(format, options)` "queries SVG DOM" directly. That repeats the current global-selector pattern in DiagramBuilder.svelte and makes the utility less testable and less reusable. It should take an explicit `SVGSVGElement`.
- **MEDIUM:** Lazy-loading a ~160KB variable font on first click conflicts with D-02's "instant download, no spinner." First export latency is likely to be noticeable unless the cache is warmed earlier.
- **MEDIUM:** The plan over-indexes on pure unit tests. Most failures here happen at browser boundaries: `Image`, canvas, serialized SVG, and download behavior.
- **LOW:** The plan does not explicitly say how it validates that every `<image>` is already a data URL. Current nodes do use `logo_base64` data URLs in SystemCard and ProspectNode, but the export step should still assert that invariant.
- **LOW:** SVG tool compatibility is still an assumption. Embedded WOFF2 is likely fine in browser-based consumers, but "opens correctly in vector tools" needs a named acceptance target.

**Suggestions**

- Change the API to something like `exportDiagram(svgEl, { format, customerName, title })` and keep DOM lookup in the component.
- Replace string rewriting with `cloneNode` + `DOMParser/XMLSerializer` manipulation of `<defs>`, markers, dimensions, and `<style>`.
- Add a dedicated UTF-8-safe `svgStringToDataUrl()` helper.
- Warm the font cache on builder mount or idle time, not on the first export click.
- Add at least one rendered integration test using `DiagramRenderer`, a base64 logo, a monogram, non-ASCII text, and each connection type.
- Reuse the same serialization path for thumbnails so the blob-URL logic in DiagramBuilder.svelte does not diverge from export behavior.
- Explicitly add XML declaration and width/height while preserving the existing `viewBox` from DiagramRenderer.svelte.

**Risk Assessment**

`MEDIUM` — the architecture is good and scoped correctly, but the plan is under-specified in the exact places export pipelines usually break: UTF-8 encoding, DOM-safe SVG rewriting, first-export performance, and browser-level integration testing.

## Plan 04-02: ExportDropdown Component

**Summary**

This is the right amount of UI for the phase. It fits the existing builder header and matches the project's current dropdown/toast patterns. The main issue is not scope; it is that the plan assumes a few interaction details that are easy to get wrong in Svelte/shadcn-style UI, especially disabled tooltips and determining when the diagram is actually "empty."

**Strengths**

- Correct dependency ordering: UI waits until the export engine exists.
- Scope stays on the frontend; no unnecessary backend work.
- Matches the user decisions closely: single Export button, PNG/SVG items, disabled when empty.
- Reuses established project patterns for dropdowns and toast errors.

**Concerns**

- **MEDIUM:** Disabled tooltips are usually tricky because disabled buttons do not emit hover/focus events. A plain disabled `Button` inside `Tooltip.Trigger` often will not show anything.
- **MEDIUM:** `hasUserSystems` is underspecified. Export should stay disabled for a prospect-only / empty diagram, and the renderer can still show a synthetic prospect even when there are no actual systems.
- **MEDIUM:** There is no automated test plan here. Manual verification alone is weak for such a small but user-facing control.
- **LOW:** No re-entry guard is mentioned. If export is async and the user clicks twice, duplicate downloads are possible.
- **LOW:** The component plan does not say how it passes the target SVG element into the utility. If `04-01` keeps global DOM querying, this plan inherits that fragility.

**Suggestions**

- Implement the disabled tooltip with a wrapper element around the disabled button, not the disabled button itself.
- Define `hasUserSystems` explicitly as "at least one non-prospect user-added system."
- Add component tests for disabled state, menu rendering, `exportDiagram('png')`, `exportDiagram('svg')`, and toast on thrown error.
- Pass an explicit SVG ref into the utility rather than letting the utility query `document`.
- Add a silent in-flight guard so repeated clicks do nothing without introducing a spinner.
- Expand manual verification to include non-ASCII names, every connection type/direction, and a cold first export.

**Risk Assessment**

`MEDIUM` — the UI work is small, but the plan leaves enough ambiguity around disabled behavior, emptiness detection, and verification that regressions are plausible unless those details are nailed down before implementation.

---

## Consensus Summary

### Agreed Strengths
- **Variable font decision is correct** — Both reviewers affirm overriding D-05 (400-only) in favor of the Inter variable font covering weights 500-700 actually used in SVG components
- **Utility-first architecture** — Both praise the standalone testable export module rather than embedding logic in the Svelte component
- **Canvas safety via data URL** — Both agree using base64 data URLs instead of blob URLs for the Image source is the right call
- **Pitfall awareness** — Both acknowledge the plan proactively addresses context-stroke, btoa overflow, Unicode encoding, and font weight issues
- **Correct dependency ordering** — Wave 1 (engine) before Wave 2 (UI) is the right sequencing

### Agreed Concerns
- **Logo inlining is implicit, not explicit** (MEDIUM) — Both note EXPO-03 is claimed "pre-solved" by Phase 1 architecture but the export plan doesn't explicitly verify/assert that all `<image>` elements are already base64 data URLs
- **First-export latency from lazy font loading** (MEDIUM) — Both flag that lazy-loading ~160KB on first click conflicts with D-02's "instant download" promise; suggest warming the cache earlier
- **String manipulation brittleness** (MEDIUM) — Codex specifically calls this HIGH; Gemini notes the complexity of context-stroke rewriting. Both suggest the approach is fragile against SVG structure changes
- **Disabled tooltip may not fire on disabled buttons** (MEDIUM, Codex) — The tooltip-on-disabled-button pattern is notoriously unreliable across component libraries
- **No automated tests for Plan 02** (MEDIUM, Codex) — Manual verification alone is weak for a user-facing control

### Divergent Views
- **Overall risk level**: Gemini rates **LOW**, Codex rates **MEDIUM**. Gemini focuses on the proven thumbnail pattern being a solid foundation; Codex focuses on under-specification at browser boundaries and UTF-8 edge cases
- **String vs DOM manipulation**: Codex strongly advocates replacing regex-based string surgery with `DOMParser`/`cloneNode` manipulation. Gemini accepts the string approach but flags SVG growth concerns. Worth investigating — DOM manipulation is more robust but harder to unit test in jsdom
- **API signature**: Codex suggests passing `SVGSVGElement` explicitly to the utility; Gemini does not raise this concern. Passing the element would improve testability but changes the ergonomics
- **Re-entry guard**: Only Codex mentions the double-click risk. Low severity but worth a simple boolean guard
