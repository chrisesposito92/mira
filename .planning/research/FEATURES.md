# Feature Research

**Domain:** Integration architecture diagram configurator (sales/SE tooling)
**Researched:** 2026-03-23
**Confidence:** HIGH

---

## Context Notes

This is NOT a general-purpose diagramming tool. It is a **configurator-style** builder that produces
branded, m3ter-style integration architecture diagrams. The output audience is prospects and customers
in sales proposals and presentations — not developers, not DevOps teams.

Key distinctions from tools like Lucidchart/draw.io:
- Output consistency over freeform flexibility
- Branded visual identity over generic shapes
- Speed for SEs over power for architects
- Export images over interactive embeds

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features a Solutions Engineer expects any diagram tool to have. Missing any of these = the tool
feels half-built and SEs will go back to slides.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Add / remove system nodes | Core building block of any diagram tool | LOW | Configurator means form-driven add, not drag-drop |
| Define connections between nodes | Required to show integration topology | LOW | Directional arrows with connection type |
| Connection type labeling | SEs need to communicate data flow semantics | LOW | Color-coded pill labels: Native Connector / Webhook+API / Custom Build |
| Named, persistable diagrams | Users expect work to be saved | LOW | Supabase-backed, tied to customer name |
| Diagram list view | Navigate between saved diagrams | LOW | Customer name + last-edited timestamp |
| PNG export | Primary output format for slides/proposals/email | MEDIUM | Must be high-resolution (2x pixel ratio) for print/presentation quality |
| SVG export | Required for scalable use in design tools | MEDIUM | Vector quality for proposals and pitch decks |
| Edit an existing diagram | Return to and revise saved work | LOW | Re-open from list → mutate configurator state |
| Undo / redo | Universal expectation in any editor | MEDIUM | Command history with reasonable depth (20-50 ops) |
| m3ter as hub node | The entire diagram topology is m3ter-centric; this must be locked | LOW | Non-removable, centered, labeled with m3ter capability names |
| System/node component library | Users expect a searchable catalogue of known systems | MEDIUM | Pre-seeded with m3ter's native connectors + common systems |
| Company logos on system nodes | SEs need customer-recognizable logos for presentations | MEDIUM | Brandfetch or Logo.dev API for on-demand fetch; fallback to initials |
| Live diagram preview | Users expect to see what they're building as they build | MEDIUM | Reactive rendering alongside configurator form |
| Grouped system categories | Prospect stacks have natural groupings (Finance, CRM, etc.) | LOW | Front Office / Finance / Analytics / Data / Custom groupings |
| Duplicate a diagram | Create a variant without starting over | LOW | Copy-on-write in DB |

### Differentiators (Competitive Advantage)

Features that generic tools like draw.io or Lucidchart cannot offer for this specific use case.
These are the reasons SEs use this tool instead of those.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| m3ter visual brand fidelity | Exported diagrams match m3ter's own marketing materials — navy background, white card containers, green m3ter accent, color-coded data flow pills, dashed connections | HIGH | This IS the core value. Every layout/rendering decision must serve this. |
| Pre-seeded m3ter native connector library | SEs immediately see Salesforce, NetSuite, Stripe, etc. as known system types with correct metadata | MEDIUM | Seed from docs.m3ter.com/guides/integrations: Finance (Stripe, NetSuite, QuickBooks, Xero, AWS/Azure Marketplace), CRM (Salesforce, HubSpot), CPQ (Paddle, Chargebee), Webhooks |
| "Your Product/Platform" customizable top node | First node SEs configure is the prospect's own product name — feels immediately personalized | LOW | Text input on hub node above m3ter |
| Connection type color coding with semantic meaning | Native Connector (green) / Webhook+API (blue) / Custom Build (orange) signals engineering effort at a glance | LOW | Competitors let you color anything; this assigns meaning to colors |
| Configurator guarantees polish | No matter the SE's design skill level, output is always on-brand and consistent | HIGH | The entire architecture decision: form-driven → branded template renderer. No freeform drag/position. |
| Custom node with logo fetch | SE can add any prospect-specific system not in the library by typing its name | MEDIUM | Logo.dev or Brandfetch API lookup by domain/name; graceful fallback |
| Internal m3ter capability labels | m3ter node shows internal capability names (Rating Engine, Ingest API, Config API, etc.) | LOW | Positions m3ter as a platform, not a black box |
| Diagram linked to Project | Optional link to an existing MIRA Project scopes diagrams to use case context | LOW | Foreign key to projects table, nullable |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem natural for a "diagram tool" but would actively undermine this product's purpose.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Freeform drag-and-drop canvas | "I want to position nodes exactly where I want" | Destroys consistent branded output; SEs with poor layout taste produce ugly diagrams; kills the core value proposition | Configurator assigns positions by algorithm; trust the layout over manual placement |
| Real-time multiplayer collaboration | "Multiple SEs might work on the same diagram" | Adds significant WebSocket/CRDT complexity; SEs are individual contributors, not pairs | Duplicate + share pattern: one SE owns a diagram, copies to hand off |
| Versioning and diff between diagram versions | "Show me what changed since last week" | Engineering cost out of proportion to actual SE need; proposals are snapshots not living docs | Last-edited timestamp + duplicate-before-edit workflow is sufficient |
| Interactive HTML / embeddable diagram export | "Can I embed this in a web page?" | No immediate SE need; adds rendering complexity; images suffice for all proposal channels | PNG/SVG export covers 100% of stated use cases (slides, PDFs, email) |
| Annotations and callout notes on diagram | "Let me add a note explaining this connection" | SEs add context in their slide decks, not the diagram image; annotations clutter the visual | Keep the exported diagram clean; SEs annotate in their deck |
| AI-generated diagram from text prompt | "Describe the integration and AI draws it for me" | LLM-generated topologies will have hallucinated connections; SE validation is the quality gate | Configurator is already faster than AI + correction cycle for constrained topology |
| Auto-discovery / live integration status | "Pull from m3ter to show what's actually connected" | Requires prod m3ter API access per customer; security/scoping nightmare; diagram is a SALES artifact not a monitoring dashboard | Manual configuration by SE is correct — it reflects what will exist, not what does exist |
| General shape library (flowcharts, UML, etc.) | "I want to use this for other diagram types" | Scope creep turns it into a worse Lucidchart; the value is m3ter-specificity | MIRA is an m3ter tool; SEs use draw.io for generic needs |
| Template marketplace / community sharing | "Let me share my diagram template" | Premature for v1 before usage patterns are known; library curation cost | Seed a few well-considered category groupings; expand after real usage |

---

## Feature Dependencies

```
[Diagram list view]
    └──requires──> [Persistable diagrams (Supabase)]
                       └──requires──> [Diagram entity schema (DB)]

[Edit existing diagram]
    └──requires──> [Persistable diagrams (Supabase)]
    └──requires──> [Configurator state hydration from saved data]

[Live preview]
    └──requires──> [Configurator state model (nodes + connections)]
    └──enhances──> [m3ter brand fidelity renderer]

[PNG/SVG export]
    └──requires──> [m3ter brand fidelity renderer]
    └──requires──> [Canvas/SVG rendering engine (e.g. Konva or pure SVG)]

[Company logos on nodes]
    └──requires──> [Logo API integration (Brandfetch or Logo.dev)]
    └──enhances──> [m3ter brand fidelity renderer]

[Custom node support]
    └──requires──> [Logo API integration]
    └──requires──> [User-defined node name input]

[Pre-seeded native connector library]
    └──requires──> [Component library data model]
    └──enhances──> [Custom node support] (library is the starting point; custom extends it)

[Duplicate diagram]
    └──requires──> [Persistable diagrams]

[Diagram linked to Project]
    └──requires──> [Persistable diagrams]
    └──requires──> [Project entity (already exists in MIRA)]

[Undo / redo]
    └──requires──> [Configurator state model]
    └──conflicts──> [Persistent auto-save] (must not save mid-undo-chain)
```

### Dependency Notes

- **PNG/SVG export requires the brand fidelity renderer**: The renderer is the critical-path component. Everything else depends on it being correct and high-quality.
- **Logo API is a shared dependency**: Both the pre-seeded library (for displaying logos) and custom node support (for fetching new logos) use the same underlying logo API integration. Build once, use everywhere.
- **Configurator state model must be serializable**: The state that drives live preview must be the same state serialized to Supabase. No separate "DB model" vs "UI model" divergence.
- **Undo/redo conflicts with auto-save**: Auto-save triggers on every state change; undo/redo reverses state changes. Saving mid-undo-chain creates confusion. Pattern: debounced save (500ms idle) not per-keystroke save.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what an SE needs to produce one professional diagram and use it in a proposal.

- [ ] Diagram entity: create, save, list, open, rename — tied to customer name, optional project link
- [ ] Configurator: add/remove system nodes from library, define connections between them with type + label
- [ ] Component library: pre-seeded m3ter native connectors (Salesforce, NetSuite, Stripe, QuickBooks, Xero, HubSpot, Chargebee, Paddle, Webhooks) + custom node with name input
- [ ] Company logos: Brandfetch/Logo.dev lookup per system name; letter-avatar fallback
- [ ] m3ter hub node: locked, centered, shows internal capability labels (non-removable)
- [ ] "Your Product/Platform" top node: customizable prospect name
- [ ] Connection type selector: Native Connector / Webhook+API / Custom Build with color-coded pill rendering
- [ ] Grouped system categories: Front Office / Finance / Analytics / Custom
- [ ] Live preview: reactive m3ter-branded diagram alongside configurator panel
- [ ] Branded renderer: navy background, white cards, green m3ter accent, dashed connections, colored data flow pills, company logos
- [ ] PNG export: 2x pixel ratio, named after customer + timestamp
- [ ] SVG export: full vector output
- [ ] Duplicate diagram
- [ ] Undo / redo (20-step history minimum)

### Add After Validation (v1.x)

Features to add once core is working and SEs are using it.

- [ ] Thumbnail generation for diagram list view — add after v1 when list grows beyond 5-10 diagrams and scanning becomes painful
- [ ] Diagram search/filter in list view — add when a single SE accumulates more than ~10 diagrams
- [ ] Additional system categories beyond initial seed — driven by SE requests after actual usage
- [ ] Custom node logo URL override — let SEs paste a logo URL if API lookup fails

### Future Consideration (v2+)

Features to defer until product-market fit is established and real usage patterns are clear.

- [ ] Vertical templates (AI/ML billing, IoT metering, SaaS subscription) — wait for usage patterns
- [ ] Shareable read-only link — only if SEs ask for it; exports cover current need
- [ ] Complexity scoring sidebar — only if SEs report it helps qualify deals
- [ ] Annotations / callout notes layer — only if SEs need it and it doesn't clutter branded output

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| m3ter branded renderer | HIGH | HIGH | P1 |
| Add/remove system nodes | HIGH | LOW | P1 |
| Connection type selector + labels | HIGH | LOW | P1 |
| Persistable diagrams | HIGH | LOW | P1 |
| PNG export | HIGH | MEDIUM | P1 |
| SVG export | HIGH | MEDIUM | P1 |
| Pre-seeded native connector library | HIGH | LOW | P1 |
| Company logos (Brandfetch/Logo.dev) | HIGH | MEDIUM | P1 |
| Live preview | HIGH | MEDIUM | P1 |
| Diagram list view | HIGH | LOW | P1 |
| Custom node support | MEDIUM | LOW | P1 |
| m3ter hub node (locked, centered) | HIGH | LOW | P1 |
| "Your Product/Platform" top node | HIGH | LOW | P1 |
| Grouped system categories | MEDIUM | LOW | P1 |
| Undo / redo | MEDIUM | MEDIUM | P1 |
| Duplicate diagram | MEDIUM | LOW | P2 |
| Thumbnail in list view | LOW | MEDIUM | P2 |
| Diagram search/filter | LOW | LOW | P2 |
| Diagram linked to Project | MEDIUM | LOW | P2 |
| Vertical templates | MEDIUM | HIGH | P3 |
| Shareable link | LOW | MEDIUM | P3 |
| Complexity scoring | LOW | HIGH | P3 |
| Annotations layer | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

This tool is NOT competing with Lucidchart or draw.io for general diagramming.
It is competing with: (a) an SE drawing on a whiteboard during a call, (b) an SE building slides
manually, (c) an SE copy-pasting a previous diagram and editing it in PowerPoint.

| Feature | Lucidchart / draw.io | Manual (slides/whiteboard) | MIRA Diagram Builder |
|---------|---------------------|---------------------------|----------------------|
| Time to first diagram | 30-60 minutes (blank canvas) | 20-40 minutes | Target: 5-10 minutes |
| Brand consistency | None (generic shapes) | Variable (copy-paste degradation) | Guaranteed by configurator |
| m3ter native connector library | None | None | Pre-seeded from m3ter docs |
| Export quality | High (generic) | Variable | High + on-brand |
| Connection semantics | Generic labels | Freeform text | Typed (Native/Webhook/Custom) |
| Persistence | Yes (files/cloud) | Inconsistent | Yes (Supabase, project-linked) |
| Undo/redo | Yes | No | Yes |
| Collaboration | Real-time | None | Single-user v1 |
| Logo handling | Manual upload or basic search | Manual | Automatic via Logo API |
| Setup overhead | Account + learning curve | Zero | Zero (inside MIRA, already authenticated) |

---

## Sources

- [m3ter integrations documentation](https://docs.m3ter.com/guides/integrations) — native connector list (Finance, CRM, CPQ, Webhooks)
- [Lucidchart vs draw.io 2026 — SelectHub](https://www.selecthub.com/diagram-software/lucidchart-vs-draw-io/) — feature coverage comparison
- [Top 8 diagramming tools for software architecture — IcePanel](https://icepanel.io/blog/2025-09-03-top-8-diagramming-tools-for-software-architecture) — configurator vs freeform analysis
- [Konva.js SVG/Canvas export docs](https://konvajs.org/docs/data_and_serialization/High-Quality-Export.html) — PNG pixelRatio export pattern
- [svelte-konva](https://github.com/konvajs/svelte-konva) — Svelte canvas binding for rendering
- [Brandfetch Logo API](https://brandfetch.com/developers/logo-api) — logo API (Clearbit replacement)
- [Logo.dev](https://www.logo.dev/) — alternative logo API
- [Clearbit API sunset Dec 2025](https://clearbit.com/changelog/2025-06-10) — do NOT use Clearbit; it is dead
- [DoiT Cloud Diagrams](https://www.doit.com/platform/cloud-diagrams/) — architecture configurator with structured node management
- [Miro architecture diagram features](https://miro.com/diagramming/software-architecture-diagram/) — connection labels and data flow patterns
- [mockflow architecture diagram tools 2025](https://mockflow.com/blog/best-architecture-diagram-tools) — table stakes feature survey

---
*Feature research for: m3ter Integration Architecture Diagram Configurator*
*Researched: 2026-03-23*
