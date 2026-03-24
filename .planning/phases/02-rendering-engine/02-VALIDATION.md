---
phase: 2
slug: rendering-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.0 + @testing-library/svelte |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run` |
| **Full suite command** | `cd frontend && npx vitest run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run`
- **After every plan wave:** Run `cd frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | 01 | 1 | REND-01 | unit | `cd frontend && npx vitest run src/lib/utils/diagram-layout.test.ts -x` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | REND-04 | unit | `cd frontend && npx vitest run src/lib/utils/diagram-layout.test.ts -x` | ❌ W0 | ⬜ pending |
| TBD | 02 | 1 | REND-02 | unit | `cd frontend && npx vitest run src/lib/components/diagram/DiagramRenderer.svelte.test.ts -x` | ❌ W0 | ⬜ pending |
| TBD | 02 | 1 | REND-03 | unit | `cd frontend && npx vitest run src/lib/components/diagram/DiagramRenderer.svelte.test.ts -x` | ❌ W0 | ⬜ pending |
| TBD | 02 | 1 | COMP-05 | unit | `cd frontend && npx vitest run src/lib/components/diagram/nodes/HubNode.svelte.test.ts -x` | ❌ W0 | ⬜ pending |
| TBD | 02 | 1 | COMP-04 | unit | `cd frontend && npx vitest run src/lib/components/diagram/nodes/ProspectNode.svelte.test.ts -x` | ❌ W0 | ⬜ pending |
| TBD | 02 | 1 | REND-05 | unit | `cd frontend && npx vitest run src/lib/components/diagram/nodes/GroupCard.svelte.test.ts -x` | ❌ W0 | ⬜ pending |
| TBD | 03 | 2 | CONN-04 | unit | `cd frontend && npx vitest run src/lib/components/diagram/connections/ConnectionLine.svelte.test.ts -x` | ❌ W0 | ⬜ pending |
| TBD | 04 | 2 | COMP-02 | unit | `cd frontend && npx vitest run src/lib/components/diagram/AddCustomSystemDialog.svelte.test.ts -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/lib/utils/diagram-layout.test.ts` — stubs for REND-01, REND-04 (pure function layout tests)
- [ ] `src/lib/components/diagram/DiagramRenderer.svelte.test.ts` — stubs for REND-02, REND-03
- [ ] `src/lib/components/diagram/nodes/HubNode.svelte.test.ts` — stubs for COMP-05
- [ ] `src/lib/components/diagram/nodes/ProspectNode.svelte.test.ts` — stubs for COMP-04
- [ ] `src/lib/components/diagram/nodes/GroupCard.svelte.test.ts` — stubs for REND-05
- [ ] `src/lib/components/diagram/connections/ConnectionLine.svelte.test.ts` — stubs for CONN-04
- [ ] `src/lib/components/diagram/AddCustomSystemDialog.svelte.test.ts` — stubs for COMP-02
- [ ] `src/lib/stores/diagrams.svelte.test.ts` — stubs for store extension (currentDiagram, updateContent)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Navy background renders correctly | REND-02 | Visual color verification | Open diagram editor, verify background is #1a1f36 |
| Logo images display in cards | REND-05 | Base64 image rendering in SVG | Create diagram with component library systems, verify logos visible |
| Connection pill labels readable | CONN-04 | Visual text readability | Add connections, verify pill text is legible at normal zoom |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
