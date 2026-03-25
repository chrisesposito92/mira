---
phase: 4
slug: export-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
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
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run `cd frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | EXPO-04 | unit | `cd frontend && npx vitest run` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | EXPO-01 | unit | `cd frontend && npx vitest run` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | EXPO-02 | unit | `cd frontend && npx vitest run` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | EXPO-01, EXPO-02 | unit | `cd frontend && npx vitest run` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | EXPO-03 | unit | `cd frontend && npx vitest run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/lib/services/export-service.test.ts` — stubs for EXPO-01, EXPO-02, EXPO-04
- [ ] Test mocks for XMLSerializer, Canvas API, Blob/URL in jsdom environment

*Existing Vitest infrastructure covers framework needs — no new framework install required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PNG is sharp on Retina | EXPO-01 | Visual quality check | Export PNG, open on Retina display, verify text/logos are crisp at zoom |
| SVG opens in vector tools | EXPO-02 | Requires external tool | Export SVG, open in Figma/Illustrator, verify paths and text intact |
| Font renders without install | EXPO-04 | Cross-machine test | Export SVG, open on machine without Inter font, verify text renders correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
