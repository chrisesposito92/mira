---
phase: 1
slug: data-foundation
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-23
audited: 2026-03-25
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (backend) / vitest 4.x (frontend) |
| **Config file** | `backend/pyproject.toml` / `frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && source .venv/bin/activate && python -m pytest tests/test_api_diagrams.py tests/test_api_component_library.py tests/test_api_logos.py -x -q` |
| **Full suite command** | `cd backend && source .venv/bin/activate && python -m pytest tests/test_api_diagrams.py tests/test_api_component_library.py tests/test_api_logos.py -v && cd ../frontend && npx vitest run src/lib/stores/diagrams.svelte.test.ts` |
| **Estimated runtime** | ~1 second (backend) + ~1 second (frontend) |

---

## Sampling Rate

- **After every task commit:** Run quick backend tests
- **After every plan wave:** Run full suite (backend + frontend)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Requirement | Description | Test File(s) | Test Count | Status |
|-------------|-------------|-------------|------------|--------|
| PERS-01 | Save diagram with customer name | `test_api_diagrams.py::TestCreateDiagram` (4), `diagrams.svelte.test.ts::createDiagram` (1) | 5 | ✅ green |
| PERS-07 | schema_version field | `test_api_diagrams.py::TestCreateDiagram::test_schema_version` | 1 | ✅ green |
| COMP-01 | Pre-populated system nodes with logos | `test_api_component_library.py::TestListComponents` (4) | 4 | ✅ green |
| COMP-03 | Systems in grouped categories | `test_api_component_library.py::TestListComponents::test_categories` | 1 | ✅ green |
| COMP-06 | Logo proxy (base64, SSRF protection) | `test_api_logos.py` (21) | 21 | ✅ green |
| NAV-01 | Sidebar "Diagrams" section | Manual-only (see below) | — | ✅ manual |
| NAV-02 | Diagram linked to project | `test_api_diagrams.py::TestCreateDiagram::test_create_with_project_id` | 1 | ✅ green |
| NAV-03 | Create new diagram | `test_api_diagrams.py::TestCreateDiagram` (4), `diagrams.svelte.test.ts::createDiagram` (1) | 5 | ✅ green |
| NAV-04 | Delete a diagram | `test_api_diagrams.py::TestDeleteDiagram` (1), `diagrams.svelte.test.ts::deleteDiagram` (1) | 2 | ✅ green |

**Additional coverage (not requirement-mapped):**

| Area | Test File | Test Count | Status |
|------|-----------|------------|--------|
| Diagram list (empty, data, excludes content, includes thumbnail) | `test_api_diagrams.py::TestListDiagrams` | 4 | ✅ green |
| Diagram get + not found | `test_api_diagrams.py::TestGetDiagram` | 2 | ✅ green |
| Diagram update (customer_name, not_found, content JSONB) | `test_api_diagrams.py::TestUpdateDiagram` | 3 | ✅ green |
| Component get + not found | `test_api_component_library.py::TestGetComponent` | 2 | ✅ green |
| DiagramStore editor (load, save, content, systems, clear) | `diagrams.svelte.test.ts::editor extension` | 11 | ✅ green |
| DiagramStore connections (add, remove, update, cascade) | `diagrams.svelte.test.ts::connection CRUD` | 10 | ✅ green |
| DiagramStore list methods (load, create, delete) | `diagrams.svelte.test.ts::existing methods` | 3 | ✅ green |

**Totals:** 42 backend tests + 24 frontend tests = **66 automated tests** covering Phase 1

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. pytest and vitest are already configured with fixtures and test patterns. No new test framework installation needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sidebar "Diagrams" nav link visible | NAV-01 | Visual layout verification | Open app, verify "Diagrams" appears in sidebar with Network icon |
| Logo proxy returns real image (E2E) | COMP-06 | Requires Logo.dev API key | Call `GET /api/logos/proxy?domain=stripe.com`, verify base64 image response |

---

## Validation Sign-Off

- [x] All requirements have automated verify or manual-only classification
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all infrastructure needs
- [x] No watch-mode flags
- [x] Feedback latency < 25s (actual: ~2s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete (audited 2026-03-25)

---

## Validation Audit 2026-03-25

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Requirements audited | 9 |
| Automated tests | 66 |
| Manual-only items | 2 |
