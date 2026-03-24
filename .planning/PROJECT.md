# m3ter Integration Architecture Diagrammer

## What This Is

A configurator-style diagram builder inside MIRA that lets m3ter Solutions Engineers assemble branded integration architecture diagrams showing how m3ter connects to a prospect's existing tech stack. SEs configure systems and connections through a builder UI, see a live preview in m3ter's visual style, and export polished PNG/SVG images for presentations and proposals.

## Core Value

An SE can produce a professional, customer-ready integration architecture diagram in minutes instead of hand-drawing on calls or cobbling together slides.

## Requirements

### Validated

- ✓ SvelteKit frontend with Tailwind v4 + shadcn-svelte — existing
- ✓ Supabase auth (SSR, session management, route guards) — existing
- ✓ Supabase database with repository pattern — existing
- ✓ FastAPI backend with async handlers — existing
- ✓ Project entity model (customer-scoped) — existing

### Active

- [ ] Top-level "Diagrams" nav section accessible from sidebar
- [ ] Diagram entity tied to a customer name, optionally linked to a Project
- [ ] Component library with m3ter native connector systems (from docs.m3ter.com/guides/integrations) plus custom nodes
- [ ] Company logos for all systems in the component library
- [ ] Custom node support (user-defined name, optional logo fetch)
- [ ] Configurator UI to add systems, define connections, set data flow direction and labels
- [ ] Color-coded connection types: Native Connector (green), Webhook/API (blue), Custom Build (orange)
- [ ] Live preview rendering in m3ter's branded visual style (navy background, white card containers, green m3ter accent, company logos, colored data flow pills, dashed connection lines)
- [ ] Grouped system categories (Front Office Stack, Finance Stack, Analytics Stack, etc.) with sub-items and multiple logos
- [ ] m3ter always centered as the hub node with internal capability labels
- [ ] "Your Product/Platform" customizable top node for the prospect's product
- [ ] Export to PNG and SVG
- [ ] Diagrams persisted to Supabase — revisitable and editable
- [ ] Diagram list view with customer name, last edited, thumbnail

### Out of Scope

- Vertical templates (AI/ML, IoT, etc.) — defer to v2 once real usage patterns emerge
- Shareable read-only links / interactive HTML export — no immediate need, SEs use exported images
- Complexity scoring sidebar — nice-to-have, not core to adoption
- Annotations and callout notes — defer, SEs can add notes in their slide decks
- Versioning and changelog between diagram versions — defer to v2
- Data flow auto-suggestions based on system types — defer, manual labeling is fine for v1
- Integration status auto-detection — defer, manual tagging is sufficient
- Drag-and-drop WYSIWYG canvas editing — configurator approach chosen for reliability and polish consistency
- Real-time collaboration / multiplayer editing — not needed, individual SE tool

## Context

- MIRA is an existing monorepo (SvelteKit frontend + FastAPI backend) with Supabase for auth and data
- This feature lives inside the same frontend, sharing auth, layout, and navigation
- The diagram output must match m3ter's existing visual style seen in their marketing/sales materials: navy background, white rounded cards with subtle shadows, company logos, green m3ter accent, color-coded data flow pill labels, dashed connection lines with dot endpoints
- m3ter has native connectors documented at docs.m3ter.com/guides/integrations — these should be the seed data for the component library
- SEs use these diagrams in proposals, follow-up emails, and presentations — the export image quality must be high enough for professional contexts
- The configurator approach was chosen over WYSIWYG canvas to guarantee consistent, polished output regardless of user skill

## Constraints

- **Tech stack**: Must use existing MIRA stack (SvelteKit, Tailwind v4, shadcn-svelte, Supabase, FastAPI)
- **Visual fidelity**: Exported diagrams must look comparable to m3ter's existing branded architecture diagrams
- **Logo sourcing**: Need a reliable approach for company/tool logos (bundled SVGs, CDN, or API)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Configurator over WYSIWYG canvas | Guarantees polished output, faster to build, no drag-precision issues | — Pending |
| Top-level nav (not nested under Projects) | Diagrams may be created before a Project exists; optional linking preserves flexibility | — Pending |
| Export to image only (no interactive HTML) | SEs primarily embed in slides/proposals; simplifies v1 scope | — Pending |
| Defer templates to v2 | Let real usage data drive which vertical patterns to templatize | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-23 after initialization*
