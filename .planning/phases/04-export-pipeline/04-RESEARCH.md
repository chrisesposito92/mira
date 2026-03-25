# Phase 4: Export Pipeline - Research

**Researched:** 2026-03-25
**Domain:** Client-side SVG/PNG export with font inlining
**Confidence:** HIGH

## Summary

Phase 4 implements a client-side export pipeline for the integration architecture diagram. The core pipeline serializes the live SVG DOM element via XMLSerializer, injects a base64-encoded Inter font as an `@font-face` rule into the SVG, then either downloads the SVG directly or renders it through an Image-to-Canvas pipeline for PNG export at 2x resolution (2400x1600).

The existing `generateAndPersistThumbnail()` function in DiagramBuilder.svelte is a working prototype of this exact pipeline at thumbnail scale (300x200). The export service generalizes this pattern at higher resolution with font injection. All logos are already base64 data URLs from Phase 1, so EXPO-03 (canvas taint from external images) is pre-solved.

**Primary recommendation:** Build a standalone `exportDiagram()` utility function in `$lib/utils/export-diagram.ts`. Use the Inter variable font (single woff2, ~160KB) to cover all weights (500, 600, 700) used in the SVG components. Fix the `context-stroke` SVG marker issue before export by rewriting marker fill attributes in the serialized SVG string.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Header toolbar dropdown -- single "Export" button in DiagramBuilder header bar, clicking opens dropdown with "Export as PNG" and "Export as SVG"
- D-02: Instant download -- click triggers download immediately, no spinner or progress bar
- D-03: Export disabled when empty -- dropdown only activates when at least one system node exists; disabled state shows tooltip
- D-04: Embed Inter as base64 @font-face -- bundle Inter woff2 as static asset, base64-encode at export time, inject into SVG style block
- D-05: Regular (400) weight only -- one woff2 file, ~90KB overhead per export (NOTE: research finding contradicts this -- see Font Weight section)
- D-06: Customer name as filename -- slugified customer_name, fallback to title, then "integration-diagram"
- D-07: Always 2x resolution -- export at 2400x1600, no resolution picker
- D-08: Native Canvas API -- XMLSerializer to Image to Canvas pattern (no html-to-image library)
- D-09: Serialize SVG with embedded font -- XMLSerializer captures SVG, inject @font-face, output as .svg file

### Claude's Discretion
- Export service architecture (standalone utility vs. store method vs. component-level function)
- Exact dropdown component choice (shadcn DropdownMenu or custom)
- SVG style injection approach (prepend to existing SVG or wrapper)
- Slugify implementation for filename generation
- Download trigger mechanism (Blob URL + anchor click vs. other)
- Error handling for edge cases (canvas security errors, font load failures)
- Whether to preload the font file at page load or lazy-load at export time

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXPO-01 | User can export diagram as PNG at 2x resolution (HiDPI) | Canvas API pipeline pattern proven in thumbnail code; scale to 2400x1600 with `canvas.toBlob('image/png')` |
| EXPO-02 | User can export diagram as SVG | XMLSerializer serialization + XML declaration prepend + Blob download |
| EXPO-03 | All logos pre-fetched to data URLs before export | Already satisfied by Phase 1 architecture -- logos stored as base64 in DB and rendered inline |
| EXPO-04 | Fonts inlined into export output for consistent rendering | Base64 @font-face injection into SVG `<style>` block before serialization |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack**: SvelteKit, Tailwind v4, shadcn-svelte, Svelte 5 runes
- **Svelte 5 only**: Use `$state`, `$derived`, `$effect` -- no legacy stores
- **shadcn-svelte components**: Use existing DropdownMenu, Button, Tooltip from `$lib/components/ui/`
- **Icons**: lucide-svelte (Download, Image, FileCode)
- **Toasts**: svelte-sonner for error notifications
- **TypeScript**: `lang="ts"` on all script blocks
- **Path aliases**: `$lib`, `$components`, `$stores`, `$services`, `$types`
- **Test runner**: Vitest with jsdom environment, `@testing-library/svelte`
- **CSS**: Tailwind v4 with `@theme inline` blocks
- **Formatting**: Prettier with tab indentation, double quotes

## Standard Stack

### Core (already installed -- no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SvelteKit | 2.50+ | Framework | Already in project |
| Svelte 5 | 5.51+ | Component model | Already in project |
| shadcn-svelte | 1.1 | UI components (DropdownMenu, Button, Tooltip) | Already installed |
| lucide-svelte | 0.575 | Icons (Download, Image, FileCode) | Already in project |
| svelte-sonner | 1.0.7 | Toast notifications for errors | Already in project |
| Vite | 7.3 | Asset handling for woff2 import | Already in project |

### New Dependencies

None required. The entire export pipeline uses native browser APIs (XMLSerializer, Canvas, Blob, URL.createObjectURL). No new npm packages needed.

### Font Asset (new file, not a package)

| Asset | Source | Size | Purpose |
|-------|--------|------|---------|
| `inter-latin-wght-normal.woff2` | `@fontsource-variable/inter` package or Google Fonts CDN | ~160KB (raw), ~213KB base64-encoded | All weights 100-900 in single file |

**NOTE on D-05 (Regular 400 only):** The actual SVG components use font-weight 500 (SystemCard, GroupItem, ConnectionPill, HubNode capabilities), 600 (ProspectNode, GroupCard, MonogramSvg), and 700 (HubNode title). A single 400-weight file would force the browser to synthesize bold, producing inferior faux-bold rendering in exports. The variable font approach (single file, all weights) is the correct solution. The file is ~160KB woff2 vs ~23KB for a single weight, but covers all the weights actually used.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Variable font woff2 (~160KB) | Static 400-weight only (~23KB) | Smaller file but faux-bold on 500/600/700 text -- visually degraded exports |
| Native Canvas API | html-to-image library | Library adds dependency, same underlying approach, less control |
| Blob URL + anchor click download | FileSaver.js | FileSaver.js adds dependency for something achievable in ~5 lines of native code |
| Manual slugify function | slugify npm package | Simple regex replacement doesn't warrant a dependency |

## Architecture Patterns

### Recommended Project Structure

```
frontend/src/lib/
  assets/
    fonts/
      inter-latin-wght-normal.woff2    # Variable Inter font (new)
  utils/
    export-diagram.ts                    # Export service (new)
    export-diagram.test.ts              # Unit tests (new)
  components/
    diagram/
      builder/
        ExportDropdown.svelte           # Export UI component (new)
```

### Pattern 1: Standalone Export Utility (Recommended)

**What:** A pure function module `exportDiagram(format, options)` that handles the entire pipeline.
**When to use:** When export logic is stateless and doesn't need reactive store access.
**Why:** Keeps DiagramBuilder thin, makes the pipeline independently testable, follows the project's existing utility pattern (see `diagram-layout.ts`).

```typescript
// $lib/utils/export-diagram.ts

export type ExportFormat = 'png' | 'svg';

export interface ExportOptions {
  customerName: string;
  title: string;
}

/**
 * Export the current diagram as PNG or SVG.
 * Queries the live SVG element, injects fonts, and triggers download.
 */
export async function exportDiagram(
  format: ExportFormat,
  options: ExportOptions,
): Promise<void> {
  const svgElement = document.querySelector('svg[role="img"]');
  if (!svgElement) throw new Error('SVG element not found');

  const serialized = new XMLSerializer().serializeToString(svgElement);
  const withFont = await injectFont(serialized);
  const withFixedMarkers = fixContextStroke(withFont);
  const filename = generateFilename(options.customerName, options.title, format);

  if (format === 'svg') {
    downloadSvg(withFixedMarkers, filename);
  } else {
    await downloadPng(withFixedMarkers, filename);
  }
}
```

### Pattern 2: Font Loading with Module-Level Cache

**What:** Lazy-load the woff2 file on first export, cache the base64 result for the session.
**When to use:** Always -- avoids loading ~160KB font until user actually exports.

```typescript
let cachedFontBase64: string | null = null;

async function loadFontBase64(): Promise<string> {
  if (cachedFontBase64) return cachedFontBase64;

  const fontUrl = new URL('$lib/assets/fonts/inter-latin-wght-normal.woff2', import.meta.url);
  const response = await fetch(fontUrl);
  const buffer = await response.arrayBuffer();
  const base64 = btoa(String.fromCharCode(...new Uint8Array(buffer)));

  cachedFontBase64 = base64;
  return base64;
}
```

**IMPORTANT:** The `btoa(String.fromCharCode(...spread))` pattern can fail for large arrays (stack overflow). For a ~160KB file, use a chunked approach:

```typescript
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
```

### Pattern 3: SVG Font Injection via String Manipulation

**What:** Insert a `<style>` block with `@font-face` into the serialized SVG string.
**When to use:** After XMLSerializer serialization, before download or canvas rendering.

```typescript
function injectFont(svgString: string, fontBase64: string): string {
  const fontFace = `
    <style>
      @font-face {
        font-family: 'Inter';
        font-style: normal;
        font-display: swap;
        font-weight: 100 900;
        src: url(data:font/woff2;base64,${fontBase64}) format('woff2');
      }
    </style>`;

  // Insert after the opening <svg ...> tag
  return svgString.replace(/(<svg[^>]*>)/, `$1${fontFace}`);
}
```

### Pattern 4: PNG Canvas Pipeline at 2x

**What:** SVG string to Image to Canvas to Blob to download.
**When to use:** PNG export path (EXPO-01).

```typescript
async function downloadPng(svgString: string, filename: string): Promise<void> {
  // Use data URL (NOT createObjectURL) to avoid canvas taint in some browsers
  const base64Svg = btoa(unescape(encodeURIComponent(svgString)));
  const dataUrl = `data:image/svg+xml;base64,${base64Svg}`;

  const img = new Image();
  img.width = 1200;
  img.height = 800;

  await new Promise<void>((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error('Failed to load SVG image'));
    img.src = dataUrl;
  });

  const canvas = document.createElement('canvas');
  canvas.width = 2400;  // 2x
  canvas.height = 1600; // 2x
  const ctx = canvas.getContext('2d')!;
  ctx.drawImage(img, 0, 0, 2400, 1600);

  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob(resolve, 'image/png');
  });

  if (!blob) throw new Error('Canvas export failed');
  triggerDownload(blob, filename);
}
```

### Pattern 5: Blob Download Trigger

**What:** Create a temporary anchor element, set href to blob URL, programmatically click.
**When to use:** All download triggers (PNG and SVG).

```typescript
function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
```

### Anti-Patterns to Avoid

- **Using `createObjectURL` for the SVG-to-Image step:** This can taint the canvas in some browsers (Chrome pre-124, Safari). Always use a data URL (`data:image/svg+xml;base64,...`) for the `img.src` when the goal is canvas rendering.
- **Spreading a large Uint8Array into String.fromCharCode:** `btoa(String.fromCharCode(...new Uint8Array(buffer)))` will throw a stack overflow for files larger than ~100KB. Use a loop instead.
- **Putting export logic in the Svelte component:** Keeps the component thin, makes the utility testable without mounting components.
- **Using `foreignObject` in any export path:** The SVG is already pure SVG with inline styles (Phase 2 decision). Do not introduce foreignObject.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dropdown menu | Custom dropdown | shadcn-svelte DropdownMenu | Already installed, handles ARIA, focus, keyboard nav |
| Tooltip | Custom tooltip | shadcn-svelte Tooltip | Already installed, handles accessibility |
| Toast notifications | Custom error UI | svelte-sonner `toast.error()` | Already in project, consistent with Phase 3 |
| Font file | Download from CDN at runtime | Bundle as static asset | Eliminates runtime network dependency, works offline |
| SVG-to-PNG | html-to-image, dom-to-image, or Puppeteer | Native XMLSerializer + Canvas API | Already proven in thumbnail code, zero dependencies |

**Key insight:** The entire export pipeline is achievable with native browser APIs. The thumbnail code is a working prototype. The only new concern is font injection and the `context-stroke` marker fix.

## Common Pitfalls

### Pitfall 1: Canvas Taint from Blob URL SVG Source
**What goes wrong:** When using `URL.createObjectURL(blob)` as the `img.src` for SVG content that will be drawn to canvas, some browsers taint the canvas, causing `canvas.toBlob()` to return null or throw a SecurityError.
**Why it happens:** Historically, Chrome and Safari treated blob-URL SVGs with certain features (foreignObject) as cross-origin, tainting the canvas. Chrome 124+ fixed this for blob URLs, but Safari behavior varies.
**How to avoid:** Use a base64 data URL (`data:image/svg+xml;base64,...`) for the `img.src` instead of a blob URL. Data URLs are never treated as cross-origin.
**Warning signs:** `SecurityError: Tainted canvases may not be exported` or `canvas.toBlob()` returning null.

### Pitfall 2: context-stroke in SVG Markers Not Rendering in Canvas Export
**What goes wrong:** The arrowhead and source-dot markers in SvgDefs.svelte use `fill="context-stroke"` (SVG2 feature) to inherit color from the parent line. When the SVG is serialized and loaded as an Image for canvas rendering, `context-stroke` may not resolve, causing markers to render as black or invisible.
**Why it happens:** The SVG-in-Image rendering pipeline doesn't fully support SVG2 context paint values in all browsers. The live DOM supports it (Chrome 124+), but the static SVG rendering path through Image may not.
**How to avoid:** After serialization, use a regex to replace `context-stroke` in marker instances with the actual stroke color from the parent line element. Alternatively, create per-connection marker defs with explicit fill colors at export time.
**Warning signs:** Black arrowheads/dots in exported PNG/SVG, or invisible markers.

### Pitfall 3: btoa() Stack Overflow on Large ArrayBuffers
**What goes wrong:** `btoa(String.fromCharCode(...new Uint8Array(buffer)))` throws `RangeError: Maximum call stack size exceeded` for files larger than ~100KB.
**Why it happens:** The spread operator creates an argument list for `String.fromCharCode()` that exceeds the JavaScript engine's call stack limit.
**How to avoid:** Use a for-loop to build the binary string character by character, then pass to `btoa()`.
**Warning signs:** Crash when converting the font file to base64.

### Pitfall 4: Font Weight Mismatch
**What goes wrong:** Exporting with only the Inter Regular (400) weight when the SVG uses font-weight 500, 600, and 700 produces faux-bold text that looks different from the live preview.
**Why it happens:** When the exact weight file isn't available, the browser synthesizes bold by algorithmically thickening glyphs, which produces inferior results.
**How to avoid:** Use the Inter variable font (single woff2 file, weight axis 100-900) instead of a single static weight file.
**Warning signs:** Text in exported diagram looks thicker/different than live preview.

### Pitfall 5: SVG Dimensions Missing in Export
**What goes wrong:** Some browsers (especially Firefox) fail to render the SVG to Image if explicit `width` and `height` attributes are missing on the root `<svg>` element.
**Why it happens:** The browser's SVG-to-raster pipeline needs explicit dimensions. The `viewBox` alone is not sufficient in all browsers.
**How to avoid:** After serialization, ensure the `<svg>` tag has explicit `width="1200"` and `height="800"` attributes. Add them if not present.
**Warning signs:** Blank/empty PNG export, especially in Firefox.

### Pitfall 6: encodeURIComponent vs btoa for SVG Data URLs
**What goes wrong:** Using `btoa()` directly on an SVG string fails if the string contains non-Latin1 characters (e.g., Unicode text in system names).
**Why it happens:** `btoa()` only accepts Latin1 (ISO 8859-1) characters. Unicode characters throw `InvalidCharacterError`.
**How to avoid:** Use `btoa(unescape(encodeURIComponent(svgString)))` to handle Unicode correctly. This first UTF-8 encodes the string, then converts to Latin1 byte string.
**Warning signs:** `InvalidCharacterError: The string to be encoded contains characters outside of the Latin1 range` when a system name contains special characters.

## Code Examples

Verified patterns from the existing codebase:

### Existing Thumbnail Pipeline (proven pattern to generalize)
```typescript
// Source: DiagramBuilder.svelte lines 111-148
const svgElement = document.querySelector('svg[role="img"]');
const svgData = new XMLSerializer().serializeToString(svgElement);
const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
const url = URL.createObjectURL(blob);

const img = new Image();
img.onload = () => {
  const canvas = document.createElement('canvas');
  canvas.width = 300;   // thumbnail: 300
  canvas.height = 200;  // thumbnail: 200
  const ctx = canvas.getContext('2d')!;
  ctx.drawImage(img, 0, 0, 300, 200);
  URL.revokeObjectURL(url);
  resolve(canvas.toDataURL('image/png', 0.8));
};
img.src = url;
```

**Key difference for export:** The thumbnail uses `createObjectURL` (blob URL) which works because it only calls `toDataURL` and the diagram has no foreignObject. For maximum safety in the export path, use a base64 data URL instead.

### SVG Font Family Currently Used in Components
```typescript
// Source: constants.ts line 65
export const SVG_FONT_FAMILY = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
```

### Font Weights Used in SVG Components
```
500: SystemCard, GroupItem, ConnectionPill, HubNode capabilities
600: ProspectNode, GroupCard, MonogramSvg
700: HubNode title ("m3ter")
```

### context-stroke Usage in SvgDefs (must fix for export)
```svelte
<!-- Source: SvgDefs.svelte -->
<marker id="arrowhead" ...>
  <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
</marker>
<marker id="source-dot" ...>
  <circle cx="5" cy="5" r="4" fill="context-stroke" />
</marker>
```

### Slugify Implementation
```typescript
// Derived from D-06 rules in CONTEXT.md
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/&/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function generateFilename(
  customerName: string,
  title: string,
  format: ExportFormat,
): string {
  const base = customerName.trim() || title.trim() || 'integration-diagram';
  return `${slugify(base)}.${format}`;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| html-to-image / dom-to-image libraries | Native XMLSerializer + Canvas API | Always available, libraries just wrap these APIs | No dependency needed; project already uses native approach for thumbnails |
| Blob URL for SVG-to-Image | Data URL for SVG-to-Image | Chrome 124 relaxed blob URL taint rules (April 2024) | Data URL approach is universally safe; blob URL now works in Chrome but not guaranteed in Safari |
| Static per-weight font files | Variable fonts (single file, all weights) | Variable font support: Chrome 66+, Firefox 62+, Safari 11+ (2018) | Single woff2 file covers weight range 100-900 |
| `context-fill` / `context-stroke` not supported | Chrome 124+ supports context paint (April 2024) | Relatively recent SVG2 feature | Live DOM rendering works, but serialized SVG in Image element may not resolve context-stroke |

## Open Questions

1. **context-stroke rendering in serialized SVG**
   - What we know: The SVG markers use `fill="context-stroke"` which works in live DOM. When serialized and loaded as Image, this may not resolve.
   - What's unclear: Whether the existing thumbnail generation already exhibits this issue (markers may be too small to notice at 300x200).
   - Recommendation: The export service MUST fix context-stroke by rewriting marker fills to explicit colors. Implement a `fixContextStroke()` function that parses the serialized SVG, finds each `<line>` element's stroke color, and creates per-color marker defs with explicit fills, or replaces the `context-stroke` with the line's stroke color in the marker reference. The simplest approach: since there are only 4 connection colors, create 4 sets of markers with explicit fills and rewrite marker-start/marker-end references per connection line.

2. **Variable font vs D-05 decision**
   - What we know: D-05 says "Regular (400) weight only, one woff2 file, ~90KB." But the SVG actually uses weights 500, 600, 700.
   - What's unclear: Whether the user would accept the variable font (~160KB woff2) for correct weight rendering vs single 400 weight (~23KB) with faux-bold.
   - Recommendation: Use the variable font. The quality difference is visible. The ~137KB size increase is negligible for an export operation (not a page load). This is a Claude's discretion area since it affects the font file choice, which is an implementation detail.

3. **Vite asset import for woff2**
   - What we know: Vite supports importing assets with `?url` suffix to get the resolved URL. Also supports static file placement in `src/lib/assets/` with the `$lib` alias.
   - What's unclear: Whether `fetch()` on an imported asset URL works correctly in all environments (dev vs build vs Vercel deployment).
   - Recommendation: Place the woff2 file in `frontend/src/lib/assets/fonts/` and use `fetch(new URL('...', import.meta.url))` or the Vite `?url` import pattern. Both are proven patterns in the Vite ecosystem.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.0 + jsdom |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test` |
| Full suite command | `cd frontend && npm run test` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXPO-01 | PNG export at 2x resolution | unit (mock Canvas/Image) | `cd frontend && npx vitest run src/lib/utils/export-diagram.test.ts -t "png"` | Wave 0 |
| EXPO-02 | SVG export with font and XML declaration | unit | `cd frontend && npx vitest run src/lib/utils/export-diagram.test.ts -t "svg"` | Wave 0 |
| EXPO-03 | Logos are base64 data URLs (pre-solved) | existing (DiagramRenderer tests) | `cd frontend && npx vitest run src/lib/components/diagram/DiagramRenderer.svelte.test.ts` | Exists |
| EXPO-04 | Font inlined as base64 @font-face | unit | `cd frontend && npx vitest run src/lib/utils/export-diagram.test.ts -t "font"` | Wave 0 |

### Testable Units (Pure Functions)
| Function | Input | Output | Testable in jsdom? |
|----------|-------|--------|-------------------|
| `slugify(text)` | string | slug string | Yes -- pure function |
| `generateFilename(customer, title, format)` | strings + format | filename string | Yes -- pure function |
| `injectFont(svgString, fontBase64)` | SVG string + base64 | SVG string with style block | Yes -- string manipulation |
| `fixContextStroke(svgString)` | SVG string | SVG string with explicit marker colors | Yes -- string manipulation |
| `arrayBufferToBase64(buffer)` | ArrayBuffer | base64 string | Yes -- pure function |

### Functions Requiring Browser API Mocks
| Function | Mock Required | Why |
|----------|---------------|-----|
| `exportDiagram(format, options)` | `document.querySelector`, `XMLSerializer` | DOM query and serialization |
| `downloadPng(svgString, filename)` | `Image`, `Canvas`, `URL.createObjectURL` | Canvas rendering pipeline |
| `loadFontBase64()` | `fetch` | Font file network request |
| `triggerDownload(blob, filename)` | `URL.createObjectURL`, `document.createElement('a')` | Browser download trigger |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run test`
- **Per wave merge:** `cd frontend && npm run test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/src/lib/utils/export-diagram.test.ts` -- covers EXPO-01, EXPO-02, EXPO-04 (pure function tests for slugify, generateFilename, injectFont, fixContextStroke, arrayBufferToBase64)
- [ ] Font file: `frontend/src/lib/assets/fonts/inter-latin-wght-normal.woff2` -- required static asset

## Sources

### Primary (HIGH confidence)
- Existing codebase: `DiagramBuilder.svelte` lines 111-148 -- proven XMLSerializer to Canvas pipeline
- Existing codebase: `SvgDefs.svelte` -- context-stroke marker usage identified
- Existing codebase: `constants.ts` -- CANVAS_WIDTH (1200), CANVAS_HEIGHT (800), SVG_FONT_FAMILY
- Existing codebase: All SVG node components -- font-weight inventory (500, 600, 700)
- MDN Web Docs: [HTMLCanvasElement.toDataURL()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toDataURL)

### Secondary (MEDIUM confidence)
- [Rendering SVG with Text to HTML Canvas](https://amxmln.com/blog/2023/rendering-svg-with-text-to-html-canvas/) -- Canvas taint from createObjectURL, data URL workaround
- [Render SVG with External Fonts to Canvas](https://alligatr.co.uk/blog/render-an-svg-using-external-fonts-to-a-canvas/) -- Base64 font injection pattern
- [Chrome Intent to Ship: SVG foreignObject blob URL taint fix](https://groups.google.com/a/chromium.org/g/blink-dev/c/JpA2vmA9XT8) -- Chrome 124 taint policy change
- [Fontsource Inter Install](https://fontsource.org/fonts/inter/install) -- Font package and file details
- [Chrome Status: context-fill and context-stroke](https://chromestatus.com/feature/5146558556536832) -- Browser support status

### Tertiary (LOW confidence)
- Inter variable font woff2 file size (~160KB for latin subset) -- from web search results, needs verification against actual file download

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all native browser APIs, proven in existing thumbnail code
- Architecture: HIGH -- direct generalization of existing `generateAndPersistThumbnail()` pattern
- Pitfalls: HIGH -- canvas taint, context-stroke, and btoa stack overflow are well-documented issues with known solutions
- Font weight concern: HIGH -- verified by direct grep of all SVG components showing weights 500, 600, 700

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain -- browser APIs don't change frequently)
