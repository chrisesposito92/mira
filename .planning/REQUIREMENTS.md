# Requirements: m3ter Integration Architecture Diagrammer

**Defined:** 2026-03-23
**Core Value:** An SE can produce a professional, customer-ready integration architecture diagram in minutes instead of hand-drawing or cobbling slides.

## v1 Requirements

### Component Library

- [x] **COMP-01**: Pre-populated system nodes for all m3ter native connectors with company logos
- [ ] **COMP-02**: User can create custom system nodes with a name and optional logo (fetched via Logo.dev)
- [x] **COMP-03**: Systems organized into grouped categories (Front Office Stack, Finance Stack, Analytics Stack, etc.)
- [x] **COMP-04**: Customizable "Your Product/Platform" prospect node with editable name
- [x] **COMP-05**: m3ter hub node always present and centered, displaying internal capability labels (Usage, Pricing, Rating, Credits, Alerts, Limits)
- [x] **COMP-06**: Backend logo proxy endpoint to convert external logos to base64 (avoids CORS/canvas taint on export)

### Connections & Data Flows

- [x] **CONN-01**: User can define connections between any two system nodes
- [x] **CONN-02**: Each connection has a direction (unidirectional or bidirectional)
- [x] **CONN-03**: Each connection has a text label describing the data flow (e.g., "Usage Events via REST API")
- [x] **CONN-04**: Connections are color-coded by integration type: Native Connector (green), Webhook/API (blue), Custom Build (orange)
- [ ] **CONN-05**: When connecting two nodes, the tool suggests common data flows based on system types
- [ ] **CONN-06**: When connecting m3ter to a known native connector system, the tool auto-tags it as "Native Connector"

### Rendering & Visual Output

- [x] **REND-01**: Live preview updates in real-time as the user configures the diagram
- [x] **REND-02**: Diagram renders in m3ter branded style: navy background, white rounded card containers, company logos, green m3ter accent border, colored data flow pill labels, dashed connection lines with dot endpoints
- [x] **REND-03**: Pure SVG rendering with inline styles (no foreignObject, no dynamic Tailwind classes)
- [x] **REND-04**: Hub-and-spoke auto-layout algorithm with m3ter centered
- [x] **REND-05**: Grouped system categories render as containing cards with sub-items and multiple logos

### Export

- [ ] **EXPO-01**: User can export diagram as PNG at 2x resolution (HiDPI for presentations)
- [ ] **EXPO-02**: User can export diagram as SVG
- [ ] **EXPO-03**: All logos pre-fetched to data URLs before export (prevents canvas taint)
- [ ] **EXPO-04**: Fonts inlined into export output for consistent rendering

### Persistence

- [x] **PERS-01**: User can save a diagram to Supabase with a customer name
- [x] **PERS-02**: Diagram list view showing customer name, last edited date
- [x] **PERS-03**: User can load and continue editing a saved diagram
- [x] **PERS-04**: Auto-save with debounced 500ms idle trigger
- [ ] **PERS-05**: Thumbnail preview generated and displayed in diagram list view
- [x] **PERS-07**: Diagram data model includes schema_version field for future migration safety

### Navigation & Organization

- [ ] **NAV-01**: Top-level "Diagrams" section in the sidebar navigation
- [x] **NAV-02**: Diagram optionally linked to an existing MIRA Project
- [x] **NAV-03**: User can create a new diagram from the Diagrams section
- [x] **NAV-04**: User can delete a diagram

## v2 Requirements

### Templates

- **TMPL-01**: Pre-built vertical templates (AI/ML Platform, IoT Provider, API-First SaaS, Fintech)
- **TMPL-02**: User can customize a template after applying it
- **TMPL-03**: User can save their own diagrams as reusable templates

### Sharing

- **SHAR-01**: Generate a read-only shareable link to view a diagram
- **SHAR-02**: Export as interactive HTML for embedding in emails/proposals

### Advanced Editing

- **EDIT-01**: Drag-and-drop WYSIWYG canvas (upgrade from configurator to interactive canvas)
- **EDIT-02**: Annotations and callout boxes with notes
- **EDIT-03**: Complexity scoring sidebar (count custom integrations, flag pain points)
- **EDIT-04**: Duplicate an existing diagram as a starting point
- **PERS-06**: User can save multiple versions of a diagram with a changelog of what changed (deferred — conflicts with PROJECT.md Out of Scope; versioning/changelog explicitly listed as out of scope for v1)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time collaboration / multiplayer | Individual SE tool, no shared editing needed |
| Mobile-responsive canvas | SEs work on desktop; diagram canvas is inherently desktop-sized |
| Server-side rendering (CairoSVG) | Client-side html-to-image is sufficient for v1 |
| Integration with external tools (Figma, Slides) | Export to image covers the workflow; direct integrations add complexity |
| Versioning and changelog (PERS-06) | PROJECT.md explicitly defers to v2; moved to v2 requirements |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| COMP-01 | Phase 1 | Complete |
| COMP-02 | Phase 2 | Pending |
| COMP-03 | Phase 1 | Complete |
| COMP-04 | Phase 2 | Complete |
| COMP-05 | Phase 2 | Complete |
| COMP-06 | Phase 1 | Complete |
| CONN-01 | Phase 3 | Complete |
| CONN-02 | Phase 3 | Complete |
| CONN-03 | Phase 3 | Complete |
| CONN-04 | Phase 2 | Complete |
| CONN-05 | Phase 3 | Pending |
| CONN-06 | Phase 3 | Pending |
| REND-01 | Phase 2 | Complete |
| REND-02 | Phase 2 | Complete |
| REND-03 | Phase 2 | Complete |
| REND-04 | Phase 2 | Complete |
| REND-05 | Phase 2 | Complete |
| EXPO-01 | Phase 4 | Pending |
| EXPO-02 | Phase 4 | Pending |
| EXPO-03 | Phase 4 | Pending |
| EXPO-04 | Phase 4 | Pending |
| PERS-01 | Phase 1 | Complete |
| PERS-02 | Phase 3 | Complete |
| PERS-03 | Phase 3 | Complete |
| PERS-04 | Phase 3 | Complete |
| PERS-05 | Phase 3 | Pending |
| PERS-06 | v2 | Deferred |
| PERS-07 | Phase 1 | Complete |
| NAV-01 | Phase 1 | Complete |
| NAV-02 | Phase 1 | Complete |
| NAV-03 | Phase 1 | Complete |
| NAV-04 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 31 active (PERS-06 deferred to v2 — conflicts with PROJECT.md Out of Scope)
- Mapped to phases: 31
- Unmapped: 0

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after roadmap creation — traceability complete, PERS-06 moved to v2*
