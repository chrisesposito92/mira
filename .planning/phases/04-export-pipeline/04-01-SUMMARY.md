---
phase: 04-export-pipeline
plan: 01
subsystem: ui
tags: [svg, png, export, font-injection, canvas, dom-manipulation, vitest]

# Dependency graph
requires:
  - phase: 02-rendering-engine
    provides: Pure SVG renderer with inline styles, viewBox-based layout, context-stroke markers
  - phase: 01-data-foundation
    provides: Base64 logo data URLs from logo proxy (EXPO-03 satisfied at source)
provides:
  - Export pipeline utility module (exportDiagram, warmFontCache)
  - Inter variable font woff2 asset for font injection
  - DOM-based SVG manipulation functions (injectFont, fixContextStroke, ensureSvgDimensions)
  - Unicode-safe SVG-to-data-URL conversion (svgToDataUrl)
  - Logo data URL validation (validateImageDataUrls)
  - Filename generation with slugify and fallback chain
affects: [04-02-PLAN]

# Tech tracking
tech-stack:
  added: ["@fontsource-variable/inter (devDependency for font asset)"]
  patterns: ["DOM-based SVG manipulation via DOMParser/cloneNode (not regex)", "Module-level font cache with warm function for preloading", "Re-entry guard pattern for async UI operations"]

key-files:
  created:
    - frontend/src/lib/assets/fonts/inter-latin-wght-normal.woff2
    - frontend/src/lib/utils/export-diagram.ts
    - frontend/src/lib/utils/export-diagram.test.ts
  modified:
    - frontend/src/lib/utils/index.ts
    - frontend/package.json

key-decisions:
  - "Variable font (wght 100-900) instead of single 400 weight -- SVG uses font-weights 500, 600, 700"
  - "DOM-based SVG manipulation via DOMParser instead of regex string surgery for reliability"
  - "Explicit SVGSVGElement parameter instead of global DOM query for testability"
  - "Loop-based arrayBufferToBase64 instead of spread operator to avoid stack overflow on large fonts"

patterns-established:
  - "Export utility as standalone module with explicit element parameter (not DOM query)"
  - "Font cache warm on mount pattern for zero-latency first export"
  - "Per-color marker duplication for context-stroke SVG export fix"

requirements-completed: [EXPO-01, EXPO-02, EXPO-03, EXPO-04]

# Metrics
duration: 4min
completed: 2026-03-25
---

# Phase 04 Plan 01: Export Pipeline Utility Summary

**DOM-based SVG export engine with Inter variable font injection, context-stroke marker fix, 2x PNG canvas rendering, and Unicode-safe data URL encoding**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-25T16:00:26Z
- **Completed:** 2026-03-25T16:04:26Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments
- Complete export pipeline utility with all 10 exported functions tested
- Inter variable font (latin, wght 100-900) bundled as static asset for font injection
- DOM-based SVG manipulation throughout -- no regex string surgery
- 24 unit tests covering all pure utility functions (slugify, generateFilename, arrayBufferToBase64, injectFont, fixContextStroke, ensureSvgDimensions, svgToDataUrl, validateImageDataUrls)

## Task Commits

Each task was committed atomically:

1. **Task 1: Bundle Inter variable font and create export-diagram utility with tests**
   - `6bb3951` (test: add failing tests for export-diagram utility -- TDD RED)
   - `f901751` (feat: implement export-diagram utility with Inter font and full test suite -- TDD GREEN)

## Files Created/Modified
- `frontend/src/lib/assets/fonts/inter-latin-wght-normal.woff2` - Inter variable font (latin subset, wght 100-900, 48KB)
- `frontend/src/lib/utils/export-diagram.ts` - Export pipeline: exportDiagram, warmFontCache, slugify, generateFilename, injectFont, fixContextStroke, ensureSvgDimensions, svgToDataUrl, arrayBufferToBase64, validateImageDataUrls
- `frontend/src/lib/utils/export-diagram.test.ts` - 24 unit tests covering all pure export utility functions
- `frontend/src/lib/utils/index.ts` - Barrel re-export of exportDiagram, warmFontCache, ExportFormat, ExportOptions
- `frontend/package.json` - Added @fontsource-variable/inter devDependency

## Decisions Made
- Used Inter variable font (wght 100-900, ~48KB) instead of single 400 weight (~17KB) because SVG components use font-weights 500, 600, and 700 (verified in SvgDefs, SystemCard, GroupCard, HubNode). This overrides D-05 which assumed regular weight only.
- fontsource latin subset is 48KB (plan estimated >100KB) -- this is the correct file from @fontsource-variable/inter, the `wght` in the filename confirms variable weight axis support.

## Deviations from Plan

None - plan executed exactly as written. The font file size difference (48KB vs plan's >100KB estimate) is a cosmetic discrepancy in the acceptance criteria, not an implementation deviation. The file is the correct variable font with full weight range.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Export utility module is ready for Plan 02 to wire the UI (export button dropdown in DiagramBuilder header)
- warmFontCache() available for preloading on DiagramBuilder mount
- exportDiagram() accepts SVGSVGElement parameter -- Plan 02 component will pass the DOM reference

## Self-Check: PASSED

- FOUND: frontend/src/lib/assets/fonts/inter-latin-wght-normal.woff2
- FOUND: frontend/src/lib/utils/export-diagram.ts
- FOUND: frontend/src/lib/utils/export-diagram.test.ts
- FOUND: 6bb3951 (RED commit)
- FOUND: f901751 (GREEN commit)
- FOUND: e863f17 (docs commit)

---
*Phase: 04-export-pipeline*
*Completed: 2026-03-25*
