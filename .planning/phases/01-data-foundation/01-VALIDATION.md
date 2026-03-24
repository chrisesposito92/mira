---
phase: 1
slug: data-foundation
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-23
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (backend) / vitest 4.x (frontend) |
| **Config file** | `backend/pyproject.toml` / `frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q --timeout=10 -m "not integration"` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v -m "not integration" && cd ../frontend && npm run test` |
| **Estimated runtime** | ~15 seconds (backend) + ~8 seconds (frontend) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q -m "not integration"`
- **After every plan wave:** Run full suite (backend + frontend)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| Populated during planning | - | - | - | - | - | - | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. pytest and vitest are already configured with fixtures and test patterns. No new test framework installation needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sidebar "Diagrams" nav link visible | NAV-01 | Visual layout verification | Open app, verify "Diagrams" appears in sidebar with Network icon |
| Logo proxy returns image from same origin | COMP-06 | Requires Logo.dev API key | Call `GET /api/logos/proxy?domain=stripe.com`, verify base64 response |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 25s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
