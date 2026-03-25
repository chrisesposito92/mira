---
phase: 4
slug: export-pipeline
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-25
audited: 2026-03-25
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.x (frontend) |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd frontend && npx vitest run` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run `cd frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Path | Status |
|---------|------|------|-------------|-----------|-------------------|-----------|--------|
| 04-01-01 | 01 | 1 | EXPO-04 warmFontCache error/caching | unit | `cd frontend && npx vitest run src/lib/utils/export-diagram.test.ts` | `frontend/src/lib/utils/export-diagram.test.ts` | green |
| 04-01-02 | 01 | 1 | EXPO-01 slugify/filename/arrayBuffer/svgToDataUrl/validateImages | unit | `cd frontend && npx vitest run src/lib/utils/export-diagram.test.ts` | `frontend/src/lib/utils/export-diagram.test.ts` | green |
| 04-01-03 | 01 | 1 | EXPO-02 SVG XML declaration + integration pipeline | unit+integration | `cd frontend && npx vitest run src/lib/utils/export-diagram.test.ts` | `frontend/src/lib/utils/export-diagram.test.ts` | green |
| 04-02-01 | 02 | 2 | EXPO-01, EXPO-02 ExportDropdown logic | unit | `cd frontend && npx vitest run src/lib/components/diagram/builder/ExportDropdown.svelte.test.ts` | `frontend/src/lib/components/diagram/builder/ExportDropdown.svelte.test.ts` | green |
| 04-02-02 | 02 | 2 | EXPO-03 hasUserSystems disabled check | unit | `cd frontend && npx vitest run src/lib/components/diagram/builder/ExportDropdown.svelte.test.ts` | `frontend/src/lib/components/diagram/builder/ExportDropdown.svelte.test.ts` | green |

*Status: pending -- green -- red -- flaky*

---

## Nyquist Audit Results

**Audited:** 2026-03-25
**Gaps filled:** 3/3
**Tests added:** 9 new tests (33 total in export-diagram.test.ts, 10 in ExportDropdown.svelte.test.ts)
**Full suite:** 274 tests, 27 files, all green

### Gap 1: SVG XML declaration (EXPO-02) -- FILLED
- Test: `SVG XML declaration (EXPO-02) > downloadSvg prepends XML declaration to SVG content via exportDiagram`
- Verifies that `exportDiagram()` with `format: 'svg'` produces a Blob whose content starts with `<?xml version="1.0" encoding="UTF-8"?>\n`
- Approach: Mocks fetch/DOM download infrastructure, calls `exportDiagram`, captures and reads Blob text

### Gap 2: SVG export integration pipeline (EXPO-02) -- FILLED
- Test: `SVG export integration pipeline (EXPO-02) > full pipeline produces SVG with font injected, markers fixed, and dimensions set`
- Test: `SVG export integration pipeline (EXPO-02) > pipeline handles SVG with no markers or images gracefully`
- Runs all exported functions in sequence on a single SVG document, verifies combined output has: font @font-face, color-specific markers, rewritten marker URLs, explicit dimensions, percentage style removed

### Gap 3: warmFontCache() caching and error behavior (EXPO-04) -- FILLED
- Test: `warmFontCache (EXPO-04) > does not throw when fetch fails (silent error handling)`
- Test: `warmFontCache (EXPO-04) > does not throw when fetch returns non-ok response`
- Test: `warmFontCache (EXPO-04) > resolves successfully when fetch succeeds`
- Verifies silent failure contract: warmFontCache catches all errors and resolves undefined

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Canvas 2x PNG rendering pipeline | EXPO-01 | jsdom has no Canvas/Image APIs | Export PNG, verify image dimensions are 2400x1600 in file properties |
| PNG is sharp on Retina | EXPO-01 | Visual quality check | Export PNG, open on Retina display, verify text/logos are crisp at zoom |
| SVG opens in vector tools | EXPO-02 | Requires external tool | Export SVG, open in Figma/Illustrator, verify paths and text intact |
| Font renders without install | EXPO-04 | Cross-machine test | Export SVG, open on machine without Inter font, verify text renders correctly |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete (Nyquist audit 2026-03-25)

---

## Validation Audit 2026-03-25

| Metric | Count |
|--------|-------|
| Gaps found | 4 |
| Resolved (automated) | 3 |
| Escalated (manual-only) | 1 |
| Tests before | 34 (24 + 10) |
| Tests after | 43 (33 + 10) |
