---
phase: 02-rendering-engine
plan: 01
subsystem: ui
tags: [svg, layout-algorithm, typescript, tdd, diagram-rendering]

requires:
  - phase: 01-data-model
    provides: DiagramSystem and DiagramContent types, ComponentLibraryItem type

provides:
  - SVG rendering constants (colors, sizes, spacing) for all diagram components
  - PositionedSystem, PositionedGroup, LayoutResult, NodePositionMap types
  - Hub-and-spoke layout algorithm as pure function
  - Text truncation utility for SVG overflow prevention
  - Edge anchor calculation for connection line termination
  - Monogram parser for logo fallback rendering
  - Explicit role field on DiagramSystem for prospect/hub identification

affects: [02-02, 02-03, 02-04, 02-05, 04-export]

tech-stack:
  added: []
  patterns:
    - Pure function layout algorithm with no DOM dependencies
    - Zone-based radial positioning with BBox-aware buffering
    - Parametric line-rect intersection for edge anchors
    - Monogram regex parsing for SVG fallback logos

key-files:
  created:
    - frontend/src/lib/components/diagram/constants.ts
    - frontend/src/lib/utils/diagram-layout.ts
    - frontend/src/lib/utils/diagram-layout.test.ts
  modified:
    - backend/app/schemas/diagrams.py
    - frontend/src/lib/types/diagram.ts
    - frontend/src/lib/types/index.ts

key-decisions:
  - "Prospect detection uses explicit role field first, with heuristic fallback for backward compatibility"
  - "5-zone clockwise distribution (left, bottom-left, bottom, bottom-right, right) ordered by display_order"
  - "BBox buffering adds 15px radial distance per extra system above threshold of 4"
  - "Scale factor uses sqrt(15/n) when system count exceeds 15 for proportional shrinking"
  - "NodePositionMap keyed by system ID plus 'hub' for O(1) connection anchor lookup"

patterns-established:
  - "Pure layout function: layoutDiagram(content, library) => LayoutResult with no side effects"
  - "Zone-based radial positioning with dynamic buffering for group cards"
  - "Edge anchor via parametric rect intersection for clean connection termination"

metrics:
  duration: 342s
  completed: "2026-03-24T14:56:43Z"
  tasks: 3
  files: 6
---

# Phase 02 Plan 01: Layout Algorithm and SVG Constants Summary

Pure hub-and-spoke layout engine with zone-based radial positioning, BBox-aware buffering, explicit prospect role detection, and edge anchor calculation for connection lines -- all as pure functions with 19 passing tests.

## What Was Built

### SVG Constants (constants.ts)
43 exported constants covering canvas dimensions, hub/prospect positions, card styling, connection line properties, color palette (inline hex values matching UI-SPEC), font family, hub capabilities list, and text truncation limits.

### Extended Types (diagram.ts)
- Added `role?: 'prospect' | 'hub' | 'system' | null` to DiagramSystem interface (frontend) and Pydantic model (backend)
- New interfaces: PositionedSystem, PositionedGroup, NodePositionMap, LayoutResult
- All new types re-exported from barrel index.ts

### Layout Algorithm (diagram-layout.ts)
6 exported functions:
1. `layoutDiagram` -- main pure function computing hub-and-spoke positions
2. `parseMonogram` -- regex parser for `monogram:AB:#FF5722` format
3. `truncateSvgText` -- truncates long text with "..." suffix
4. `estimatePillWidth` -- estimates rendered width of connection pill labels
5. `getConnectionMidpoint` -- midpoint calculation for connection lines
6. `computeEdgeAnchor` -- parametric line-rect intersection for edge anchors

### Test Coverage (diagram-layout.test.ts)
19 tests covering:
- Empty/single/multi-system layouts
- Category grouping and zone distribution
- Prospect detection (explicit role + heuristic fallback)
- Canvas bounds enforcement
- Determinism verification
- Scale-down for 15+ systems
- BBox buffering for large groups
- Monogram parsing (valid + invalid)
- Text truncation (long + short)
- Edge anchor calculation
- NodePositionMap completeness
- Connection midpoint and pill width estimation

## Key Files

- `frontend/src/lib/components/diagram/constants.ts` -- 43 SVG rendering constants
- `frontend/src/lib/types/diagram.ts` -- Extended with role field + 4 layout types
- `frontend/src/lib/types/index.ts` -- Updated barrel exports
- `frontend/src/lib/utils/diagram-layout.ts` -- 6 exported pure functions (498 lines)
- `frontend/src/lib/utils/diagram-layout.test.ts` -- 19 tests (533 lines)
- `backend/app/schemas/diagrams.py` -- Added role field to DiagramSystem

## Decisions Made

1. **Explicit role field over heuristic-only detection** -- Addresses review HIGH concern. The `role` field on DiagramSystem provides reliable prospect/hub identification. Heuristic fallback (null component_library_id + null category) is kept only for backward compatibility with existing diagrams.

2. **NodePositionMap for O(1) anchor lookup** -- Addresses review MEDIUM-HIGH concern (connection anchor calculation). Instead of re-scanning positioned nodes, the layout result includes a flat map keyed by system ID for direct lookup by connection rendering components.

3. **BBox buffering for large groups** -- Addresses review MEDIUM concern (node collision). Groups with >4 systems are pushed radially outward by 15px per extra system, preventing overlap with adjacent zones.

4. **Text truncation utility** -- Addresses review MEDIUM concern (SVG text overflow). `truncateSvgText` clips to maxChars and appends "..." to prevent overflow in cards and pills.

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all functions are fully implemented with no placeholder data or TODO markers.

## Issues Encountered

None.

## Next Phase Readiness

- Layout algorithm ready for consumption by DiagramRenderer (Plan 02-03) via `$derived(layoutDiagram(content, library))`
- Constants ready for import by all SVG node components (Plans 02-03, 02-04)
- NodePositionMap and computeEdgeAnchor ready for connection rendering (Plan 02-04)
- Types ready for diagram store extension (Plan 02-02)

## Self-Check: PASSED

All 6 created/modified files verified present. All 3 commit hashes (65d4718, 20020b3, edf667f) verified in git log.

---
*Phase: 02-rendering-engine*
*Completed: 2026-03-24*
