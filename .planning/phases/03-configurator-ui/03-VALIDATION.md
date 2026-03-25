---
phase: 3
slug: configurator-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
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
| TBD | TBD | TBD | CONN-01 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CONN-02 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CONN-03 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CONN-05 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CONN-06 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | PERS-02 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | PERS-03 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | PERS-04 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | PERS-05 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Test stubs for store extensions (removeSystem, addConnection, removeConnection, updateConnection)
- [ ] Test stubs for auto-save $effect behavior
- [ ] Test stubs for thumbnail generation utility
- [ ] Test stubs for connection form validation

*Existing vitest infrastructure covers framework setup. Wave 0 adds test files for new Phase 3 functionality.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live SVG preview updates on system add | CONN-01 | Requires visual DOM rendering with SVG | Add system in sidebar, verify SVG re-renders with new node |
| SVG-to-canvas thumbnail fidelity | PERS-05 | Canvas rendering quality is visual | Save diagram, check thumbnail in list view matches SVG |
| Auto-save debounce timing | PERS-04 | Timing-sensitive behavior | Edit diagram, verify save indicator shows after ~500ms pause |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
