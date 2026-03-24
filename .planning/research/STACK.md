# Stack Research

**Domain:** In-app branded diagram configurator/renderer (SvelteKit add-on feature)
**Researched:** 2026-03-23
**Confidence:** HIGH (primary choices verified via npm, official docs, and Svelte Flow docs)

---

## Context

This is a stack decision for a **new feature added to an existing monorepo**. The base stack (SvelteKit, Tailwind v4, shadcn-svelte, Supabase, FastAPI, TypeScript) is already decided and locked. This document covers only the net-new libraries needed for the diagram configurator.

The diagram is a **configurator-first, not WYSIWYG**: the user assembles a diagram through a structured form UI, and a live SVG preview renders from the resulting data model. There is no drag-and-drop canvas editing. This constraint significantly narrows the choices.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `@xyflow/svelte` (Svelte Flow) | 1.5.1 | Live diagram preview rendering | The canonical node-graph library for Svelte. v1.0 was rewritten for Svelte 5 runes (`$state.raw` for nodes/edges). Actively maintained by the xyflow team (same authors as React Flow). MIT licensed. **However, see the Architecture note below — Svelte Flow may be overkill for this configurator pattern.** |
| Custom SVG (no lib) | n/a | Static diagram rendering | The diagram has a fixed hub-and-spoke topology with m3ter always centered. Positions are deterministic from the data model, not user-dragged. A hand-authored Svelte SVG component gives exact visual control, zero bundle overhead, and no CORS issues on export. This is the **primary recommendation** for the preview renderer. |
| `html-to-image` | **pin 1.11.11** | PNG export from DOM node | The official Svelte Flow export example uses this library and explicitly pins to 1.11.11. Versions after 1.11.11 have a known regression (open issue #516) where image export produces incorrect output. Do not upgrade until the upstream bug is resolved. |
| `@dagrejs/dagre` | 3.0.0 | Auto-layout fallback (future) | If the diagram ever needs auto-layout (e.g., variable number of spokes, template mode), dagre provides a simple directed-graph layout. The original `dagre` package is abandoned; `@dagrejs/dagre` is the maintained fork. For v1 with a fixed hub-and-spoke topology, this is **not needed** — positions are hardcoded from a polar coordinate formula. |

### Logo Sourcing

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Logo.dev CDN | n/a | Company logo images for system nodes | Free tier: 500,000 requests/month with attribution. URL pattern: `https://img.logo.dev/{domain}?token={api_token}&format=webp&size=128&retina=true`. Clearbit's free logo API was discontinued December 1, 2025 — Logo.dev is the official migration path. For the ~30 m3ter native connectors in the seed library, logos can also be bundled as inline SVGs to avoid the CDN CORS issue on export. |
| Bundled inline SVGs | n/a | Logos for known m3ter connector systems | For the curated connector library (Salesforce, NetSuite, Stripe, etc.), bundle SVG logo files directly in the frontend as Svelte components. Zero CDN latency, zero CORS issues, works offline. Use Logo.dev only for user-defined custom nodes where the domain is unknown at build time. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `vite-plugin-svgr` or `@sveltejs/vite-plugin-svelte` SVG import | n/a | Import SVG files as Svelte components | Already in the Svelte ecosystem via SvelteKit's Vite integration. Use for bundling the curated connector SVG logos. Import as `?component` to get inline SVG. |
| `elkjs` | 0.11.1 | Advanced auto-layout (future) | Only needed if the diagram evolves to support free-form topologies or complex sub-flow layouts. Not recommended for v1. |

---

## Architecture Decision: SVG-first, not Svelte Flow

**For the v1 configurator**, use a **hand-authored reactive SVG component** rather than Svelte Flow. Here is why:

1. **Fixed topology**: m3ter is always the centered hub. System nodes orbit it in a radial or layered arrangement. Positions are computed from the data model (category grouping, index within category) — not dragged by the user. Svelte Flow's drag/pan/zoom machinery is unused weight.

2. **Export fidelity**: `html-to-image` captures whatever DOM node you give it. A plain `<svg>` element with inlined styles is the most reliable source for pixel-perfect export. No viewport transform arithmetic, no foreignObject nesting, no shadow DOM surprises.

3. **Full visual control**: The m3ter branded style (navy background, white rounded cards, dashed connection lines, colored pill labels, green accent) requires precise SVG authorship. Svelte Flow custom nodes achieve this but with more indirection. A custom SVG component achieves it directly.

4. **No CORS problem for bundled logos**: An inline `<svg>` diagram with inline SVG logos has zero cross-origin issues. For Logo.dev logos on custom nodes, proxy the image through a FastAPI endpoint (`/api/proxy/logo?domain={domain}`) that fetches and returns the logo as a base64 data URL — this is a one-liner with httpx and solves the CORS/canvas-taint problem cleanly.

**When to adopt Svelte Flow**: If a v2 requirement introduces drag-to-reposition nodes, edge reconnection, or a fully interactive canvas editor, migrate the preview renderer to Svelte Flow at that point. The data model (nodes + edges arrays) maps directly to Svelte Flow's API, so the migration is mechanical.

---

## Export Strategy

The export flow for PNG and SVG is:

```
1. Diagram data model (nodes[], edges[], layout config)
   ↓
2. Reactive SVG component renders in DOM (hidden off-screen at 2x pixel density)
   ↓
3. html-to-image@1.11.11 toPng() captures the SVG element
   ↓
4. PNG blob → download link (client-side) or return as base64 (API)
```

For SVG export: serialize the `<svg>` element's outerHTML directly. No library needed — `element.outerHTML` produces a valid, portable SVG string.

**Critical**: External logo images (from Logo.dev CDN) must be proxied and inlined as data URIs before export, or they will be blank in the output due to canvas taint security restrictions. The FastAPI proxy endpoint handles this.

---

## Logo Sourcing Strategy

| Node type | Logo source | Rationale |
|-----------|-------------|-----------|
| m3ter native connector (~30 systems) | Bundled inline SVG | Guaranteed availability, no network, no CORS, zero latency, perfect for export |
| User-defined custom node (by domain) | Logo.dev CDN → backend proxy → base64 | Logo.dev free tier (500K req/mo) is more than sufficient. Backend proxy at `/api/proxy/logo?domain=stripe.com` fetches, resizes, and returns base64. Cached in Supabase or in-memory to avoid repeat fetches. |
| Unknown domain (fallback) | Generated monogram initials | If Logo.dev returns 404 or request fails, render a colored circle with the system's initials. Purely CSS/SVG — no image dependency. |

---

## Installation

```bash
# From frontend/
npm install html-to-image@1.11.11

# Only if auto-layout is needed in a future phase:
npm install @dagrejs/dagre
npm install -D @types/dagre

# Svelte Flow (defer to future phase if interactive canvas is scoped):
npm install @xyflow/svelte
```

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| Custom SVG component | Svelte Flow | Svelte Flow is the right choice for interactive canvas editors. For a configurator with fixed topology and branded export, it adds unnecessary drag/pan machinery and complicates the export path. Revisit in v2 if interactive editing is scoped. |
| Custom SVG component | D3.js | D3's DOM manipulation model works against Svelte's reactivity. Layer Cake (Svelte wrapper around D3 concepts) is cleaner but still heavier than needed for a single diagram type with fixed layout. |
| Custom SVG component | Konva.js / svelte-konva | Canvas-based. Canvas export is straightforward, but canvas rendering produces raster artifacts at non-native scale. SVG export is lossless and scales infinitely — important for professional proposal quality. |
| Custom SVG component | Fabric.js | Same issue as Konva — canvas-based, raster output. Also not Svelte-native. |
| html-to-image@1.11.11 | html-to-image@latest | The Svelte Flow team explicitly pins to 1.11.11 due to a regression in later versions (open GitHub issue #516). Latest is 1.11.13 as of this research — do not use. |
| html-to-image | html2canvas | html2canvas has ~2.6M weekly downloads but uses a manual painting approach that becomes slow on complex DOM and has worse CSS transform support. html-to-image's SVG foreignObject approach is faster and more CSS-accurate. |
| html-to-image | snapDOM | snapDOM (v0.1.2) is very new (experimental). Promising architecture but insufficient production track record for a professional export tool. Revisit in 6 months. |
| Logo.dev | Clearbit | Clearbit's free logo API was discontinued December 1, 2025. Logo.dev is the official migration path recommended by Clearbit/HubSpot. |
| Logo.dev + backend proxy | Direct CDN `<img>` tags | Direct CDN images work in the UI but fail silently in PNG export due to browser canvas-taint security. The proxy pattern solves this definitively. |
| Bundled SVGs for known connectors | Logo.dev for all logos | Logo.dev requires a network request and API token. For the curated connector library (known at build time), bundled inline SVGs are faster, more reliable, and require no token. |
| @dagrejs/dagre | original `dagre` package | The original `dagre` package (v0.8.5) has not been updated in 6 years. `@dagrejs/dagre` (v3.0.0) is the actively maintained fork. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `dagre` (original) | Last published 6 years ago; NPM package is effectively abandoned | `@dagrejs/dagre@3.0.0` |
| `html-to-image@>1.11.11` | Known regression in export output (issue #516, still open as of 2026-03) | Pin to `html-to-image@1.11.11` |
| `Clearbit Logo API` | Discontinued December 1, 2025 | `Logo.dev` |
| `svelvet` | Last published 6 months ago (v11.0.5), shows reduced maintenance velocity compared to Svelte Flow. Not built on Svelte 5 runes. | `@xyflow/svelte` (if interactive canvas is ever needed) |
| Direct `<img src="https://img.logo.dev/...">` in exported diagrams | Canvas taint: cross-origin images cause `toDataURL()` to throw SecurityError, resulting in blank logos in PNG export | Backend proxy + base64 inline |
| Drag-and-drop canvas (WYSIWYG) in v1 | Out of scope per PROJECT.md; configurator approach was explicitly chosen for reliability and polish consistency | Configurator UI → reactive SVG preview |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `html-to-image@1.11.11` | SvelteKit (Vite), any browser | Pin exactly. Do not follow semver patch bumps until the upstream regression is fixed. |
| `@xyflow/svelte@1.5.1` | Svelte 5, SvelteKit | Fully rewritten for Svelte 5 runes in v1.0. Not compatible with Svelte 4. |
| `@dagrejs/dagre@3.0.0` | Any bundler | TypeScript types included. No separate `@types/dagre` needed for the `@dagrejs` scoped package. |

---

## Sources

- https://svelteflow.dev/ — Svelte Flow v1.5.1 confirmed, Svelte 5 runes support verified
- https://svelteflow.dev/examples/misc/download-image — html-to-image@1.11.11 pin documented, toPng() approach
- https://svelteflow.dev/learn/layouting/layouting-libraries — dagre vs elkjs trade-offs
- https://xyflow.com/blog/svelte-flow-release — v1.0 release notes, Svelte 5 rune conversion
- https://www.logo.dev/pricing — Free tier: 500,000 req/mo with attribution; Startup $280/yr
- https://developers.hubspot.com/changelog/upcoming-sunset-of-clearbits-free-logo-api — Clearbit discontinuation December 1, 2025
- https://www.logo.dev/clearbit — Official Clearbit → Logo.dev migration guide
- https://github.com/bubkoo/html-to-image — html-to-image library source and options
- npm show @xyflow/svelte version → 1.5.1 (verified 2026-03-23)
- npm show html-to-image version → 1.11.13 (latest; use 1.11.11 per Svelte Flow guidance)
- npm show @dagrejs/dagre version → 3.0.0 (verified 2026-03-23)
- npm show elkjs version → 0.11.1 (verified 2026-03-23)
- npm show svelvet version → 11.0.5, last published 6 months ago (verified 2026-03-23)

---
*Stack research for: m3ter Integration Architecture Diagram Builder (MIRA feature add-on)*
*Researched: 2026-03-23*
