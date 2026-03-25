---
phase: 3
slug: configurator-ui
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-24
audited: 2026-03-25
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest 4.0 + @testing-library/svelte |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd frontend && npx vitest run` |
| **Estimated runtime** | ~10 seconds |
| **Total tests (phase 3)** | 48 (across 4 test files + 1 backend test file) |
| **Total suite** | 268 tests, 27 files, 0 failures |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run `cd frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Test File | Tests | Status |
|---------|------|------|-------------|-----------|-----------|-------|--------|
| 03-01-01 | 01 | 1 | CONN-01 | unit | `diagrams.svelte.test.ts` | addConnection, removeConnection, updateConnection (10) | ✅ green |
| 03-01-01 | 01 | 1 | CONN-02 | unit | `diagrams.svelte.test.ts` | updateConnection direction:bidirectional (line 327) | ✅ green |
| 03-01-01 | 01 | 1 | CONN-03 | unit | `diagrams.svelte.test.ts` | addConnection label check (line 293) | ✅ green |
| 03-01-02 | 01 | 1 | PERS-02 | unit | `test_api_diagrams.py` | test_list_includes_thumbnail + list tests | ✅ green |
| 03-01-03 | 01 | 1 | PERS-04 | unit | `utils.test.ts` | debounce (3 tests) | ✅ green |
| 03-03-01 | 03 | 2 | CONN-05 | unit | `ConnectionForm.svelte.test.ts` | suggestions (5 tests: CRM, Billing, null, unknown, all 10 categories) | ✅ green |
| 03-03-01 | 03 | 2 | CONN-06 | unit | `ConnectionForm.svelte.test.ts` | auto-suggest native_connector (9 tests: hub+native, bidirectional, guard, empty, edge cases) | ✅ green |
| 03-03-01 | 03 | 2 | CONN-01 | unit | `ConnectionForm.svelte.test.ts` | HUB_ENDPOINT (3 tests: id, name, role) | ✅ green |
| 03-04-01 | 04 | 3 | PERS-04 | unit | `DiagramBuilder.svelte.test.ts` | version counter (3 tests) | ✅ green |
| 03-04-01 | 04 | 3 | PERS-05 | unit | `DiagramBuilder.svelte.test.ts` | thumbnail throttle (2 tests) | ✅ green |
| 03-04-01 | 04 | 3 | PERS-02 | unit | `utils.test.ts` | formatRelativeTime (6 tests) | ✅ green |
| 03-04-01 | 04 | 3 | PERS-03 | unit | `diagrams.svelte.test.ts` | loadDiagram (3 tests) | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*All resolved. Existing vitest infrastructure covered framework setup. Test files were created during plan execution.*

- [x] Store extension tests (removeSystem, addConnection, removeConnection, updateConnection) — `diagrams.svelte.test.ts`
- [x] Auto-save version counter tests — `DiagramBuilder.svelte.test.ts`
- [x] Thumbnail throttle tests — `DiagramBuilder.svelte.test.ts`
- [x] Connection form + suggestions tests — `ConnectionForm.svelte.test.ts`
- [x] Utility function tests (debounce, formatRelativeTime) — `utils.test.ts`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live SVG preview updates on system add | CONN-01 | Requires visual DOM rendering with SVG | Add system in sidebar, verify SVG re-renders with new node |
| SVG-to-canvas thumbnail fidelity | PERS-05 | Canvas rendering quality is visual | Save diagram, check thumbnail in list view matches SVG |
| Auto-save debounce timing | PERS-04 | Timing-sensitive $effect behavior | Edit diagram, verify save indicator shows after ~500ms pause |

*These are supplementary visual verifications. All requirements also have automated unit test coverage for their core logic.*

---

## Test File Inventory

| File | Tests | Covers |
|------|-------|--------|
| `frontend/src/lib/stores/diagrams.svelte.test.ts` | 22 | CONN-01, CONN-02, CONN-03, PERS-03 |
| `frontend/src/lib/components/diagram/builder/ConnectionForm.svelte.test.ts` | 17 | CONN-05, CONN-06, CONN-01 (hub) |
| `frontend/src/lib/components/diagram/DiagramBuilder.svelte.test.ts` | 5 | PERS-04, PERS-05 |
| `frontend/src/lib/utils.test.ts` | 13 | PERS-04 (debounce), PERS-02 (formatRelativeTime) |
| `backend/tests/test_api_diagrams.py` | 12 | PERS-02 (list + thumbnail) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-25

---

## Validation Audit 2026-03-25

| Metric | Count |
|--------|-------|
| Requirements audited | 9 |
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |

**Gap detail:**
- CONN-06 (PARTIAL → COVERED): Added 9 tests for auto-suggest `native_connector` logic — hub+native positive case, bidirectional hub detection, user override guard, empty inputs, null component_library_id, unknown system ID.
