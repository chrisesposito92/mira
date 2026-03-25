# Roadmap: m3ter Integration Architecture Diagrammer

## Overview

Four phases that build the diagrammer from the ground up: database and backend API first (the dependency root), then the SVG rendering engine and logo infrastructure (the critical-path component that unblocks everything), then the configurator UI that wires form inputs to live preview, and finally the export pipeline that wraps the completed renderer. Each phase delivers a coherent, independently verifiable capability. Export is last because it depends on a stable renderer — and the hardest export pitfalls (canvas taint, font inlining) are mitigated in Phase 2, not retrofitted.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Data Foundation** - DB schema, backend CRUD, component library seed with schema_version (completed 2026-03-24)
- [ ] **Phase 2: Rendering Engine** - SVG renderer, DiagramStore, logo proxy, inline-style color conventions
- [ ] **Phase 3: Configurator UI** - Builder layout, system picker, connection form, diagram list, auto-save
- [ ] **Phase 4: Export Pipeline** - PNG/SVG export with font inlining, 2x HiDPI, pre-fetch logo base64

## Phase Details

### Phase 1: Data Foundation
**Goal**: Backend infrastructure exists so the frontend can persist and retrieve diagrams and component library entries
**Depends on**: Nothing (first phase)
**Requirements**: PERS-01, PERS-07, NAV-01, NAV-02, NAV-03, NAV-04, COMP-01, COMP-03, COMP-06
**Success Criteria** (what must be TRUE):
  1. A diagram can be created, saved, and retrieved via the backend API with all fields intact including schema_version
  2. The component library endpoint returns seeded m3ter native connector systems organized into their categories
  3. The logo proxy endpoint accepts a domain and returns a base64-encoded image from the same origin
  4. The sidebar shows a top-level "Diagrams" navigation link
  5. A diagram can be optionally linked to an existing MIRA Project and deleted from the list view
**Plans:** 5 plans

Plans:
- [x] 01-01-PLAN.md — DB migrations (diagrams + component library), Pydantic schemas, config update
- [x] 01-02-PLAN.md — Frontend TypeScript types, diagram service factory, diagram store
- [x] 01-03-PLAN.md — Backend API routes (diagrams CRUD, component library, logo proxy), service layer, router registration
- [x] 01-04-PLAN.md — Frontend UI (sidebar nav, diagram list page, DiagramCard, CreateDiagramDialog, DeleteDiagramDialog)
- [x] 01-05-PLAN.md — Backend unit tests, logo seed script

### Phase 2: Rendering Engine
**Goal**: A live, m3ter-branded SVG diagram renders correctly from diagram data with logos and color-coded connections
**Depends on**: Phase 1
**Requirements**: REND-01, REND-02, REND-03, REND-04, REND-05, COMP-02, COMP-04, COMP-05, CONN-04
**Success Criteria** (what must be TRUE):
  1. The diagram preview renders with navy background, white rounded card nodes, green m3ter accent, dashed connection lines, and colored data flow pills
  2. m3ter is always centered as the hub node with capability labels; "Your Product/Platform" appears at the top as a customizable prospect node
  3. Grouped system categories render as containing cards with sub-items and logos visible
  4. Connection type colors (Native Connector green, Webhook/API blue, Custom Build orange) are applied via inline hex styles — not dynamic Tailwind classes
  5. A custom system node can be created with a name and logo resolved through the backend proxy with a monogram fallback
**Plans:** 5 plans

Plans:
- [x] 02-01-PLAN.md — SVG constants, layout types, hub-and-spoke layout algorithm (TDD)
- [x] 02-02-PLAN.md — DiagramStore extension (currentDiagram, componentLibrary, updateContent)
- [x] 02-03-PLAN.md — SVG node components (SvgDefs, HubNode, ProspectNode, SystemCard, GroupCard, MonogramSvg)
- [x] 02-04-PLAN.md — Connection components (ConnectionLine, ConnectionPill)
- [x] 02-05-PLAN.md — DiagramRenderer, editor route, AddCustomSystemDialog, visual verification

### Phase 3: Configurator UI
**Goal**: An SE can assemble a complete diagram through form-driven panels, see live preview, and have it persist automatically
**Depends on**: Phase 2
**Requirements**: CONN-01, CONN-02, CONN-03, CONN-05, CONN-06, PERS-02, PERS-03, PERS-04, PERS-05
**Success Criteria** (what must be TRUE):
  1. SE can browse the component library by category, add system nodes to the diagram, and see the preview update immediately
  2. SE can define a connection between any two nodes with a direction, label, and integration type selector
  3. When connecting m3ter to a known native connector system, the type is auto-suggested as "Native Connector"
  4. The diagram list shows customer name and last-edited timestamp; SE can open a saved diagram and continue editing
  5. Changes are auto-saved within 500ms of the SE stopping; a thumbnail is generated and shown in the list view
**Plans:** 4 plans
**UI hint**: yes

Plans:
- [x] 03-01-PLAN.md — Backend thumbnail in list response, DiagramStore connection CRUD + removeSystem, utility functions (debounce, formatRelativeTime)
- [x] 03-02-PLAN.md — Install shadcn components, DiagramBuilder layout + SystemPicker + SaveStatusIndicator
- [x] 03-03-PLAN.md — ConnectionForm with auto-suggest, ConnectionList, SettingsPanel
- [x] 03-04-PLAN.md — Auto-save with thumbnail generation, DiagramCard enhancement, visual verification

### Phase 4: Export Pipeline
**Goal**: An SE can export a finished diagram as a high-quality PNG or SVG suitable for slides and proposals
**Depends on**: Phase 3
**Requirements**: EXPO-01, EXPO-02, EXPO-03, EXPO-04
**Success Criteria** (what must be TRUE):
  1. SE can export the diagram as PNG at 2x resolution — image is sharp on Retina displays in presentation slides
  2. SE can export the diagram as SVG — file opens correctly in vector tools with all text and paths intact
  3. All logos are pre-fetched and inlined as base64 data URLs before export — no blank logo squares in the output
  4. Fonts render consistently in the exported file regardless of whether the receiving machine has the font installed
**Plans:** 2 plans
**UI hint**: yes

Plans:
- [ ] 04-01-PLAN.md — Export utility module (DOM-based SVG manipulation, font injection, context-stroke fix, logo validation, UTF-8-safe encoding, font cache warming) + Inter variable font asset + unit tests
- [ ] 04-02-PLAN.md — ExportDropdown component with wrapper-span tooltip + component tests, DiagramBuilder header integration with font preloading, visual verification

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation | 5/5 | Completed | 2026-03-24 |
| 2. Rendering Engine | 0/5 | Planned | - |
| 3. Configurator UI | 0/4 | Planned | - |
| 4. Export Pipeline | 0/2 | Planned | - |
