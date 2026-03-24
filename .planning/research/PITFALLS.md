# Pitfalls Research

**Domain:** Branded diagram builder — SVG rendering, logo management, export-to-image, configurator UI, node layout
**Researched:** 2026-03-23
**Confidence:** HIGH (core rendering/CORS findings verified against MDN, GitHub issues, official docs; logo API findings verified against provider docs)

---

## Critical Pitfalls

### Pitfall 1: Cross-Origin Images Taint the Export Canvas

**What goes wrong:**
At export time, `toDataURL()` or `toBlob()` throws `SecurityError: Tainted canvases may not be exported`. Any cross-origin image drawn into a `<canvas>` (including logos fetched from logo APIs, CDNs, or Supabase storage without explicit CORS headers) marks the canvas as tainted and blocks all pixel readback. This also affects the SVG-as-image route: all browsers treat an SVG with a `<foreignObject>` referencing an external URL as not origin-clean when rasterized via a canvas.

**Why it happens:**
Developers fetch logo URLs directly from a third-party API (Brandfetch, logo.dev) and set them as `<img src>` inside the diagram SVG. The browser enforces the same-origin policy on canvas operations regardless of whether the images visually displayed correctly.

**How to avoid:**
Route all logo images through a backend proxy endpoint (e.g., `GET /api/logos/proxy?domain=stripe.com`) that fetches the image server-side and serves it from the same origin with `Access-Control-Allow-Origin: *`. Set `crossOrigin="anonymous"` on every `<img>` in the diagram. Alternatively, convert logos to base64 data URIs at fetch time and embed them directly in the SVG — this is the cleanest approach for the configurator model.

**Warning signs:**
- Export works in dev but silently fails in production (different origins)
- Logo images display fine visually but export produces a broken/blank PNG
- Browser console shows `SecurityError` only on export, not on load

**Phase to address:** Logo management phase (Phase 1 / library seeding). Establish the proxy or base64-embedding pattern before the first render loop is built; retrofitting is painful.

---

### Pitfall 2: Web Fonts Disappear in SVG Export

**What goes wrong:**
The exported PNG/SVG looks correct in the browser but node labels, pill text, and category headings render in a fallback system font (or disappear entirely). This happens because SVG-as-image rendering blocks external font requests for security reasons — `@import` and `@font-face` declarations inside `<foreignObject>` or the serialized SVG string are not fetched by the browser.

**Why it happens:**
Libraries like `html-to-image` serialize the DOM into an SVG string and inject computed styles, but Google Fonts or any externally loaded typeface is not inline. The browser, when rendering the SVG as an image (via a `<canvas>` or `drawImage`), runs in a restricted context that does not allow external network requests.

**How to avoid:**
Inline the font as a base64-encoded `@font-face` block in the SVG's `<style>` element before export. Fetch the font file once, convert to base64, and inject it into the clone before rasterization. `html-to-image` has a `fetchStyle` option that attempts this automatically but it is unreliable across CORS boundaries — do it explicitly. For the m3ter brand font, bundle it in the static assets directory and serve from the same origin.

**Warning signs:**
- Fonts look correct in the live preview but wrong in exports
- Downloaded PNG uses Arial/sans-serif instead of the designed typeface
- Font renders correctly when you open the raw SVG file in a browser tab (which can fetch external resources), but not when exported

**Phase to address:** Export phase. Build a `prepareExportClone()` function that inlines fonts and base64-encodes logos before any rasterization. Never skip this even in MVP.

---

### Pitfall 3: Tailwind CSS Classes Strip Out of Exported SVG Clone

**What goes wrong:**
The diagram preview renders perfectly, but the exported image is missing rounded corners, padding, shadow effects, and color fills. The `html-to-image` / `html2canvas` clone captures `getComputedStyle()` values only for styles that are actually resolved — if Tailwind's JIT purge removed a utility class because it was dynamically constructed at runtime (e.g., `bg-${color}-500`), the computed style is empty and the clone captures nothing.

**Why it happens:**
Tailwind v4's content scanning detects class names statically. Dynamic class composition (string interpolation, conditional classes built from data) produces strings that the scanner never sees. Those classes are excluded from the output CSS, so `getComputedStyle()` returns empty values for those properties.

**How to avoid:**
Use inline `style` attributes for all values that come from diagram data (node colors, connection colors, background). Use Tailwind classes only for structural/static styles. For the three connection-type colors (green/blue/orange), hardcode the hex values in a constants file and apply them via inline style, never via a dynamic Tailwind class. This pattern also makes the SVG export cleaner because inline styles survive the serialization step without any font/class injection.

**Warning signs:**
- Diagrams look correct in the SvelteKit dev server but exported images are unstyled or partially styled
- Differences between dev and production exports (JIT is more aggressive in production builds)
- Color-coded connection pills appear gray or transparent in exports

**Phase to address:** Rendering phase (Phase 1). Establish the "inline styles for data-driven values, Tailwind for structural styles" rule in the initial diagram component.

---

### Pitfall 4: Logo API Reliability and CORS Constraints Kill the UX

**What goes wrong:**
Logos fail to load silently (404s, rate limits, CORS blocks) and the diagram shows broken image icons instead of company logos. Because SEs demo these diagrams live on calls, a broken logo at the wrong moment is embarrassing. Additionally, Clearbit's Logo API shut down December 2025 — any code referencing it is already broken.

**Why it happens:**
Developers use client-side `<img src="https://logo.dev/...">` requests directly in the browser. `logo.dev` requires a `Referer` header with the registered origin and blocks "programmatic access" (bulk fetching). Brandfetch enforces per-plan rate limits. Neither CDN is guaranteed to have logos for niche or new companies. Network failures are not caught or fallback-handled.

**How to avoid:**
1. Pre-fetch and cache logos server-side at component-library seeding time, storing the base64 or Supabase Storage URL per system.
2. For custom nodes (user-defined systems), fetch the logo via the backend proxy at node-creation time and cache the result — never fetch at render time.
3. Implement a fallback chain: cached logo → logo.dev (via proxy) → Brandfetch (via proxy) → generated monogram initials avatar.
4. Store all cached logos in Supabase Storage to survive API outages during live demos.

**Warning signs:**
- Network tab shows logo requests going directly to third-party domains from the browser
- No fallback UI when a logo 404s (diagram shows broken image icon)
- Logo fetching happens on every render instead of once at creation time

**Phase to address:** Logo management phase. The caching and fallback strategy must be designed before the component library UI is built.

---

### Pitfall 5: HiDPI / Retina Exports Look Pixelated

**What goes wrong:**
Exported PNGs look sharp on a 1x screen but appear blurry or pixelated when inserted into a MacBook Retina presentation. SEs use these images in slide decks viewed on 2x–3x displays. A canvas exported at CSS pixel dimensions (e.g., 1200×800px) renders at half the required pixel density on a Retina display.

**Why it happens:**
Canvas elements have a logical size (CSS pixels) and a physical size (device pixels). By default, `toBlob()` exports at 1x. `window.devicePixelRatio` on the export machine may be 1 (server-side render, CI, standard monitor) so developers never notice the blur.

**How to avoid:**
Always export at a fixed multiplier of at least 2x regardless of the current device. When drawing to the export canvas: set `canvas.width = logicalWidth * 2` and `canvas.height = logicalHeight * 2`, then `ctx.scale(2, 2)` before drawing. Offer a "2x / 3x" export option in the UI. For SVG export, SVGs are resolution-independent by nature — prefer SVG export when the target is presentations, and generate PNG from the SVG at 2x for embedding contexts.

**Warning signs:**
- Export looks sharp on the developer's 1x monitor but blurry in slide deck screenshots
- Text and logo edges appear jagged at 100% zoom in presentation software
- The export pixel dimensions exactly match the CSS canvas size

**Phase to address:** Export phase. Build the 2x scale into the export function from day one — it is not possible to retroactively upgrade without changing the export API surface.

---

### Pitfall 6: Diagram JSON Schema Breaks Saved Diagrams on Field Rename

**What goes wrong:**
A saved diagram that worked perfectly in Phase 1 fails to load after Phase 2 renames a field in the JSON schema (e.g., `node.type` becomes `node.systemType`, or connection color codes change). Old diagrams stored in Supabase silently fail to render, showing empty canvases or partial diagrams with no error message.

**Why it happens:**
The diagram state (nodes, connections, positions) is stored as a JSONB column. There is no migration applied to existing rows when the schema evolves — the old data just stops matching the new code's expectations.

**How to avoid:**
Include a `schema_version` field (integer) in every diagram's root JSON from day one. Write a `migrateSchema(diagram, currentVersion)` function that handles each version transition. Apply migrations on read (lazy migration) so existing diagrams are always upgraded when loaded. Keep migration functions permanently — never delete them. For MVP, version 1 is fine, but the version field must exist from the start.

**Warning signs:**
- No `schema_version` field in the diagram JSON structure
- Code that reads `diagram.nodes[i].type` without handling missing or renamed fields
- Tests that only load freshly-created diagrams, never deserialized old fixtures

**Phase to address:** Data model phase (earliest possible). Add `schema_version: 1` to the TypeScript type definition before persisting a single diagram.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Fetch logos client-side directly from logo API | No backend changes needed | Tainted canvas on export, rate limit exposure, CORS failures in production | Never — proxy is required |
| Use dynamic Tailwind classes for connection colors | Less code | Classes purged in production builds, broken exports | Never — use inline styles for data-driven colors |
| Export at 1x resolution | Simpler export code | Blurry images in Retina presentations, SE complaints | Never for the m3ter use case |
| Skip `schema_version` field in v1 | Faster initial delivery | Cannot safely evolve the schema; old diagrams break silently | Never — 5-minute addition with permanent value |
| Skip font inlining in export | Export works in dev | Text renders in wrong font in all exported images | Never — embed fonts or the export feature is broken |
| Render the preview using the same DOM tree that gets exported | Simpler code | Export captures UI chrome (scrollbars, selection highlights, edit handles) | Only if export is always a separate render function |
| Store logos as CDN URLs in the DB | Simpler initially | Diagrams break when logo CDN changes URLs or goes down | Never for production — store in Supabase Storage |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| logo.dev / Brandfetch | Direct client-side fetch without `Referer` header; treating `<img src>` as sufficient | Backend proxy endpoint; store fetched images in Supabase Storage; fallback to monogram |
| Supabase Storage (logo cache) | Using public bucket URLs directly as `<img src>` in export canvas | Fetch the image via authenticated API, convert to base64 before export |
| html-to-image / html2canvas | Calling `toPng()` on the live preview DOM (which has edit UI overlays) | Export a separate headless render-only clone with no interactive elements |
| Canvas `toBlob()` | Not awaiting all images to load before calling export | Use `Promise.all()` on image load events; add `crossOrigin="anonymous"` before setting `src` |
| SvelteKit SSR | Importing canvas/SVG manipulation libraries at module level | Wrap in `onMount` or `import()` dynamically; canvas APIs do not exist on the server |
| Supabase JSONB | Storing diagram state without a version field | Always include `schema_version` and write migration functions |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-fetching logos on every component mount | Network waterfall on diagram open; logos flash in | Cache logos in the store on first fetch; never re-fetch if already in state | Immediately, even with 5 nodes |
| SVG DOM with too many elements (1500+ nodes) | Sluggish hover/click interactions; style recalculations stall | This app has ~10–30 nodes per diagram (hub-spoke model); SVG is appropriate; do not add animation loops | Not a concern for this scale |
| Generating a thumbnail on every save | Save latency spikes; blocked UI on autosave | Generate thumbnails asynchronously after save confirms; use a low-res 400px snapshot | At > a few saves per session |
| Deep reactive watchers on the full diagram state | Every keystroke in a label field re-renders the full canvas | Use fine-grained Svelte 5 `$state` per node/connection; avoid deriving the entire diagram in one reactive block | Immediately noticeable during label editing |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing raw logo API keys in frontend env vars | Key exposed to all browser clients; rate limits burned by users | Keep API keys server-side only; all logo fetches go through the FastAPI backend |
| Trusting the `domain` parameter in the logo proxy without validation | SSRF — attacker uses the proxy to fetch internal services | Validate domain is a public hostname; block RFC1918 addresses; allow only HTTP/HTTPS schemes |
| Rendering user-supplied node labels via `{@html}` | XSS — attacker injects script via a diagram label | Always render labels as text nodes, never as raw HTML; use Svelte's default text interpolation |
| Embedding user-uploaded logos without content-type validation | SVG with embedded JavaScript passes through as an "image" | Validate content-type on upload; for SVGs, sanitize with a library like DOMPurify before storing |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No loading state during logo fetch | Diagram appears broken; SE may abandon | Show a spinner/skeleton in node cards during logo resolution; resolve before the diagram preview renders |
| Export button triggers immediately before logos load | PNG with broken image placeholders instead of logos | Disable export until all logo promises resolve; show a "preparing export..." state |
| Configurator allows adding a system with no logo and no fallback | Blank square in the diagram breaks visual consistency | Always generate a monogram/initial avatar as the fallback; never show a broken image |
| No confirmation before deleting a node that has connections | Silent data loss; SE loses carefully configured diagram | Show a confirmation dialog listing the N connections that will also be removed |
| Thumbnail in the diagram list is stale after edits | SE opens wrong version of a diagram thinking it is current | Regenerate thumbnail on save (async); show "last edited" timestamp prominently |
| Diagram preview and exported image look different | SE shares an export that does not match what they approved | Use the same rendering path for preview and export; do not apply UI-only styles to the live preview component |

---

## "Looks Done But Isn't" Checklist

- [ ] **Logo rendering:** Logos display in the live preview — verify they also appear correctly in an exported PNG (cross-origin taint check)
- [ ] **Font rendering:** Custom fonts display in the live preview — verify they are embedded and appear in the exported SVG/PNG
- [ ] **HiDPI export:** Export PNG looks sharp on a 1x monitor — verify at 2x zoom or on a Retina display
- [ ] **Schema versioning:** Diagram saves and loads correctly today — verify a diagram saved now still loads after a field rename (load a serialized fixture)
- [ ] **Logo fallback:** All logos from logo.dev resolve — verify behavior when a logo returns 404 (monogram appears, no broken image)
- [ ] **Export isolation:** Export looks correct — verify no selection highlights, hover states, or edit handles are captured in the exported image
- [ ] **CORS proxy:** Logos load in dev — verify in a production-like origin (different domain, no localhost CORS exceptions)
- [ ] **Connection label wrapping:** Short labels display correctly — verify long labels do not overflow pill shapes or overlap connection lines
- [ ] **Diagram list thumbnail:** Thumbnail shows the diagram — verify thumbnail updates after edits (not just on create)
- [ ] **SSR safety:** Diagram editor loads — verify no `document is not defined` errors during server-side render (canvas libraries must be dynamically imported)

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Tainted canvas discovered post-launch | HIGH | Add backend proxy endpoint; update all logo `<img>` tags to use proxy URLs; re-test all export paths |
| Font disappears in exports | MEDIUM | Identify font files; write `inlineFont()` utility that fetches and base64-encodes; inject before export; add to export test suite |
| Schema migration needed for existing saved diagrams | MEDIUM–HIGH | Write migration script; add `schema_version` to JSONB; apply lazy migration on read; test with saved fixtures from each prior version |
| Tailwind class purging breaks exports | MEDIUM | Audit all data-driven class names; replace with inline styles; rebuild and re-test export against all diagram configurations |
| HiDPI export blur reported by users | LOW | Update export function to use 2x scale factor; no schema changes required; re-deploy |
| Logo API outage breaks diagram loading | LOW (if cached) / HIGH (if not) | If logos were cached in Supabase Storage: fallback already works. If not cached: emergency fallback to monograms; background job to re-fetch and cache |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Cross-origin canvas taint | Logo management / component library seeding phase | Export a diagram containing a logo fetched via the proxy; confirm `toBlob()` succeeds |
| Web fonts stripped from export | Export implementation phase | Export a diagram with custom fonts; open PNG in an image viewer and confirm typeface matches preview |
| Tailwind classes purged from export | Diagram rendering component (first phase) | Build a production bundle; export a diagram with all three connection colors; confirm colors appear |
| Logo API reliability | Logo management / seeding phase | Disable network; attempt to open a diagram; confirm logos load from Supabase Storage cache |
| HiDPI pixelated exports | Export implementation phase | Export a PNG; insert into a Keynote/Google Slides slide on a Retina MacBook; confirm no blur |
| Diagram JSON schema breaks on rename | Data model phase (Phase 0 / DB schema) | Deserialize a v1 fixture with the current reader code; confirm it loads without errors |
| SSR hydration crash | Rendering component setup | Run `npm run build && npm run preview`; navigate to the diagram editor; confirm no server-side errors |
| Logo dark background visibility | Diagram rendering component | Render a white-on-white logo (e.g., Apple) on the navy background; confirm it is visible |

---

## Sources

- [MDN: Use cross-origin images in a canvas](https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/CORS_enabled_image)
- [Tainted Canvas explanation (corsfix.com)](https://corsfix.com/blog/tainted-canvas)
- [Resolving tainted canvas errors with Konva](https://konvajs.org/docs/posts/Tainted_Canvas.html)
- [html-to-image GitHub README](https://github.com/bubkoo/html-to-image)
- [Snapdom: modern html2canvas alternative (DEV Community)](https://dev.to/tinchox5/snapdom-a-modern-and-faster-alternative-to-html2canvas-1m9a)
- [SVG foreignObject rendering limitations (semisignal.com)](https://semisignal.com/rendering-web-content-to-image-with-svg-foreign-object/)
- [SVG fonts in img tag not loaded (supercodepower.com)](https://supercodepower.com/en/svg-img-use-font/)
- [draw.io: why exported SVG text may not display correctly](https://www.drawio.com/doc/faq/svg-export-text-problems)
- [logo.dev rate limits](https://www.logo.dev/docs/platform/rate-limits)
- [Brandfetch rate limits](https://docs.brandfetch.com/logo-api/rate-limits)
- [Clearbit logo API sunset (HubSpot changelog)](https://developers.hubspot.com/changelog/upcoming-sunset-of-clearbits-free-logo-api)
- [LogoKit Clearbit alternative](https://logokit.com/clearbit-alternative)
- [Dagre layout limitations (React Flow docs)](https://reactflow.dev/learn/layouting/layouting)
- [SVG performance vs Canvas threshold (Hacker News)](https://news.ycombinator.com/item?id=15024190)
- [Apache ECharts: Canvas vs SVG best practices](https://apache.github.io/echarts-handbook/en/best-practices/canvas-vs-svg/)
- [devicePixelRatio for HiDPI canvas (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio)
- [SvelteKit page options — disabling SSR](https://svelte.dev/docs/kit/page-options)
- [Adaptive SVG logos for light/dark mode (getpublii.com)](https://getpublii.com/docs/prepare-svg-for-light-dark-mode.html)

---
*Pitfalls research for: m3ter Integration Architecture Diagram Builder*
*Researched: 2026-03-23*
