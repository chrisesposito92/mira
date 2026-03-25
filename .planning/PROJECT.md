# m3ter Integration Architecture Diagrammer

## What This Is

A configurator-style diagram builder inside MIRA that lets m3ter Solutions Engineers assemble branded integration architecture diagrams showing how m3ter connects to a prospect's existing tech stack. SEs configure systems and connections through a builder UI, see a live preview in m3ter's visual style, and export polished PNG/SVG images for presentations and proposals.

## Current State

**Shipped:** v1.0 MVP (2026-03-25)
**Codebase:** ~31K LOC (TypeScript/Svelte/Python)
**Tech stack:** SvelteKit + Tailwind v4 + shadcn-svelte (frontend), FastAPI + Supabase (backend), pure SVG rendering with DOM-based export

v1.0 delivers the full SE workflow: browse component library, add systems, define connections, see live branded preview, export to PNG/SVG. 31 requirements validated, 91+ tests passing.

## Core Value

An SE can produce a professional, customer-ready integration architecture diagram in minutes instead of hand-drawing on calls or cobbling together slides.

## Requirements

### Validated

- ✓ SvelteKit frontend with Tailwind v4 + shadcn-svelte — existing
- ✓ Supabase auth (SSR, session management, route guards) — existing
- ✓ Supabase database with repository pattern — existing
- ✓ FastAPI backend with async handlers — existing
- ✓ Project entity model (customer-scoped) — existing
- ✓ Top-level "Diagrams" nav section accessible from sidebar — v1.0
- ✓ Diagram entity tied to a customer name, optionally linked to a Project — v1.0
- ✓ Component library with m3ter native connector systems plus custom nodes — v1.0
- ✓ Company logos for all systems in the component library — v1.0
- ✓ Custom node support (user-defined name, optional logo fetch) — v1.0
- ✓ Live preview rendering in m3ter's branded visual style — v1.0
- ✓ Grouped system categories with sub-items and multiple logos — v1.0
- ✓ m3ter always centered as the hub node with internal capability labels — v1.0
- ✓ "Your Product/Platform" customizable top node for the prospect's product — v1.0
- ✓ Configurator UI to add systems, define connections, set data flow direction and labels — v1.0
- ✓ Color-coded connection types: Native Connector (green), Webhook/API (blue), Custom Build (orange) — v1.0
- ✓ Diagrams persisted to Supabase — revisitable and editable — v1.0
- ✓ Diagram list view with customer name, last edited, thumbnail — v1.0
- ✓ Export to PNG and SVG — v1.0

### Active

(Planning next milestone — requirements TBD via `/gsd:new-milestone`)

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
- The diagram output matches m3ter's visual style: navy background, white rounded cards with subtle shadows, company logos, green m3ter accent, color-coded data flow pill labels, dashed connection lines with dot endpoints
- 29 native connector systems seeded in component library from m3ter docs
- SEs use these diagrams in proposals, follow-up emails, and presentations — export image quality is high enough for professional contexts
- The configurator approach guarantees consistent, polished output regardless of user skill

## Constraints

- **Tech stack**: Must use existing MIRA stack (SvelteKit, Tailwind v4, shadcn-svelte, Supabase, FastAPI)
- **Visual fidelity**: Exported diagrams must look comparable to m3ter's existing branded architecture diagrams
- **Logo sourcing**: Logo.dev API via backend proxy with monogram fallback (SSRF-protected)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Configurator over WYSIWYG canvas | Guarantees polished output, faster to build, no drag-precision issues | ✓ Good — consistent output quality, built in 2 days |
| Top-level nav (not nested under Projects) | Diagrams may be created before a Project exists; optional linking preserves flexibility | ✓ Good — clean UX separation |
| Export to image only (no interactive HTML) | SEs primarily embed in slides/proposals; simplifies v1 scope | ✓ Good — PNG/SVG covers all use cases |
| Defer templates to v2 | Let real usage data drive which vertical patterns to templatize | — Pending (need usage data) |
| Pure SVG with inline styles | Avoids foreignObject and dynamic Tailwind; enables clean export | ✓ Good — no canvas taint, consistent rendering |
| DOM-based SVG manipulation for export | More reliable than regex string surgery for font injection and style fixup | ✓ Good — handles edge cases (context-stroke, markers) cleanly |
| Inter variable font (wght 100-900) | SVG uses font-weights 500/600/700; single font file covers all weights | ✓ Good — simpler than multiple font files |
| Logo proxy with SSRF protection | Multi-layer defense (FQDN regex, IP rejection, hostname blocklist, content-type, size cap) | ✓ Good — secure by default |

## Next Milestone Goals

TBD — run `/gsd:new-milestone` to define v1.1 scope based on SE feedback and usage patterns.

Candidates from v2 requirements backlog:
- Vertical templates (TMPL-01/02/03)
- Shareable links (SHAR-01/02)
- Drag-and-drop canvas (EDIT-01)
- Diagram duplication (EDIT-04)
- Versioning (PERS-06)

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
*Last updated: 2026-03-25 after v1.0 milestone*
