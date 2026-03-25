# Phase 4: Export Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 04-export-pipeline
**Areas discussed:** Export trigger UX, Font inlining, File naming, PNG resolution

---

## Export Trigger UX

| Option | Description | Selected |
|--------|-------------|----------|
| Header toolbar dropdown | Single "Export" button in header, dropdown with PNG/SVG options | ✓ |
| Export dialog with options | Modal dialog with format, resolution, filename preview | |
| Inline split button | Split button: "Export PNG" default, chevron reveals SVG | |

**User's choice:** Header toolbar dropdown
**Notes:** Minimal UI, consistent with existing header pattern.

| Option | Description | Selected |
|--------|-------------|----------|
| Instant download | Click triggers download immediately, no spinner | ✓ |
| Brief toast notification | Toast showing "Exporting..." then confirmation | |
| You decide | Claude picks based on performance | |

**User's choice:** Instant download
**Notes:** Export should complete sub-second given inline-style SVG.

| Option | Description | Selected |
|--------|-------------|----------|
| Disabled when empty | Export only activates with at least one system node | ✓ |
| Always available | Let SE export even an empty diagram | |
| You decide | Claude picks | |

**User's choice:** Disabled when empty
**Notes:** Prevents exporting a blank navy rectangle.

---

## Font Inlining

| Option | Description | Selected |
|--------|-------------|----------|
| Embed base64 @font-face | Bundle Inter woff2, inject as base64 @font-face in SVG style block | ✓ |
| System font fallback | Export with existing font stack, rely on OS defaults | |
| Convert text to paths | Use opentype.js to convert text to SVG path outlines | |

**User's choice:** Embed base64 @font-face
**Notes:** ~90KB overhead per export, guarantees pixel-perfect text everywhere.

| Option | Description | Selected |
|--------|-------------|----------|
| Regular (400) only | One woff2 file, covers all current text rendering | ✓ |
| Regular (400) + Bold (700) | Two weights, ~180KB total | |
| You decide | Claude checks actual renderer usage | |

**User's choice:** Regular (400) only
**Notes:** SVG renderer uses regular weight for all text elements.

---

## File Naming

| Option | Description | Selected |
|--------|-------------|----------|
| customer-name.ext | Slugified customer_name, fallback to title then generic | ✓ |
| customer-architecture.ext | Appends "-architecture" descriptor | |
| customer-YYYY-MM-DD.ext | Includes export date for versioning | |

**User's choice:** customer-name.ext
**Notes:** Clean, recognizable in file lists and email attachments.

---

## PNG Resolution

| Option | Description | Selected |
|--------|-------------|----------|
| Always 2x | 2400×1600, no resolution picker | ✓ |
| Dropdown: 1x / 2x / 3x | Resolution picker in export dropdown | |
| You decide | Claude picks | |

**User's choice:** Always 2x
**Notes:** Meets EXPO-01 exactly. Sharp on Retina, 4K, printed slides.

| Option | Description | Selected |
|--------|-------------|----------|
| Native Canvas API | Same XMLSerializer → Image → Canvas as thumbnails, zero new deps | ✓ |
| html-to-image library | Install html-to-image for edge case handling | |
| You decide | Claude picks during implementation | |

**User's choice:** Native Canvas API
**Notes:** Already proven in thumbnail code. Resolves STATE.md concern about html-to-image.

---

## Claude's Discretion

- Export service architecture (standalone utility vs. store method)
- Dropdown component choice
- SVG style injection approach
- Slugify implementation
- Download trigger mechanism
- Error handling strategy
- Font preloading vs lazy-loading

## Deferred Ideas

None — discussion stayed within phase scope.
