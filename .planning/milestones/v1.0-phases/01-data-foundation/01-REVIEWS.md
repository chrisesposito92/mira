---
phase: 1
reviewers: [gemini, codex]
reviewed_at: 2026-03-23T23:47:00Z
plans_reviewed: [01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md, 01-04-PLAN.md, 01-05-PLAN.md]
---

# Cross-AI Plan Review — Phase 1: Data Foundation

## Gemini Review

# Phase 1: Data Foundation - Structured Plan Review

## 1. Summary
Phase 1 establishes a robust, type-safe bridge between the Svelte 5 frontend and the FastAPI/Supabase backend. The architectural choices—specifically the use of Pydantic for JSONB validation and the proactive caching of logos—demonstrate a high level of engineering maturity. The plan successfully balances flexibility (storing diagram state in JSONB) with structural integrity (schema versioning and strict backend validation). The three-wave execution strategy is logically sound, ensuring that infrastructure precedes UI, and testing validates the whole.

## 2. Strengths
*   **Forward-Thinking Data Modeling:** Including `schema_version` (PERS-07) in the initial table definition is excellent. It prevents "migration debt" when the diagramming engine evolves in Phase 2/3.
*   **Strong Validation Layer:** Using nested Pydantic models (`DiagramContent`) to validate JSONB ensures the database never becomes a "garbage dump" for malformed frontend state.
*   **Performance Optimization:** Caching logos as base64 in the `component_library` table (D-06/D-07) is a superior choice over direct proxying for every request. It reduces latency and protects against Logo.dev availability issues or rate-limit exhaustion.
*   **Modern Frontend State Management:** Utilizing Svelte 5 runes (`$state`, `$derived`) in the store ensures the integration is idiomatic and performant for the target tech stack.
*   **Clear Ownership Logic:** Explicitly planning for user-id ownership checks in the service layer (Plan 01-03) ensures multi-tenant security from the start.

## 3. Concerns

*   **SSRF Risk in Logo Proxy (Plan 01-03):**
    *   **Severity: MEDIUM**
    *   The logo proxy endpoint accepts a `domain` parameter. If not strictly validated (e.g., regex for valid domain patterns), it could be exploited for Server-Side Request Forgery (SSRF) to scan internal network ports or fetch metadata from the cloud provider.
*   **Logo.dev Rate Limiting (Plan 01-05):**
    *   **Severity: LOW**
    *   The `seed_logos.py` script fetches ~30 logos. While 10k/month is plenty, the script should be idempotent and handle transient network failures or rate-limiting headers (429) gracefully to avoid partial seeds.
*   **JSONB Queryability Gaps:**
    *   **Severity: LOW**
    *   Storing connections and systems inside a single JSONB column makes it difficult to answer questions like "Which diagrams use the 'Salesforce' connector?" across the entire DB using standard SQL. (Acceptable for an MVP, but worth noting).
*   **Frontend Error Boundaries:**
    *   **Severity: LOW**
    *   The plans focus on the "happy path" of CRUD. Ensure the `DiagramStore` handles API failures (500s, 401s) without leaving the UI in a "loading" or "stale" state.

## 4. Suggestions

*   **Strict Domain Validation:** In the Logo Proxy (`backend/app/api/logos.py`), implement a strict validator that ensures the `domain` string is a valid FQDN and does not resolve to local or reserved IP ranges.
*   **Soft Deletes vs. Hard Deletes:** For `PERS-01`, consider adding a `deleted_at` timestamp rather than a hard SQL `DELETE`. SEs may accidentally delete a diagram they spent hours on; soft deletes allow for a "Trash/Restore" feature later.
*   **Thumbnail Placeholder:** Plan 01-01 includes a `thumbnail_base64` field. Ensure the migration defaults this to a generic placeholder or `NULL` so the UI doesn't break before the actual screenshotting logic is implemented in Phase 2.
*   **Component Library UUID Stability:** In `015_component_library.sql`, use hardcoded UUIDs for the seeded rows (e.g., `gen_random_uuid()` or fixed v4 UUID strings) to ensure that if the migration is re-run or used in different environments, the IDs remain stable for references.
*   **Batch Logo Fetching:** Update `seed_logos.py` to use an async HTTP client (like `httpx`) with a semaphore to limit concurrency, preventing the script from being flagged as a DoS attack by Logo.dev.

## 5. Risk Assessment

**Overall Risk: LOW**

**Justification:**
The plan uses the existing, proven tech stack and follows established patterns in the MIRA codebase. The dependencies are well-mapped, and the parallelization of Wave 1 maximizes efficiency. The technical complexity is low, primarily involving standard CRUD and one external API integration. The primary risk is security-related (SSRF), which is easily mitigated with standard input validation. The data model is robust enough to support the intended "configurator-style" builder without requiring immediate refactoring.

**Verdict:** **PROCEED TO EXECUTION** after implementing domain validation in the Logo Proxy.

---

## Codex Review

# Phase 1 Review

Overall, the wave breakdown is sensible and fits the existing MIRA architecture. The main weaknesses are under-specified API/data contracts for future editing, plus real security and operational risk around the logo proxy and logo seeding flow.

## Plan 01-01: DB Migrations, Pydantic Schemas, Config Update

**Summary**
Strong foundation plan that matches repo conventions, but a few schema decisions are still too loose for a feature that will become a long-lived builder artifact.

**Strengths**
- Good separation between user-owned `diagrams` data and shared `component_library` reference data.
- Adding `schema_version` and nested `DiagramContent` validation in Phase 1 is the right move.

**Concerns**
- `[HIGH]` Seed data safety is unclear. Plain seeded `INSERT`s will be brittle unless `component_library` has a stable unique key and upsert-safe migration logic.
- `[HIGH]` `project_id` delete behavior is unspecified. If a linked Project is deleted, diagrams should almost certainly survive with `project_id` set to `NULL`.
- `[MEDIUM]` `DiagramContent` is underspecified for migration safety: unique system IDs, connection referential integrity, and whether systems reference library items by immutable key/id are not called out.
- `[MEDIUM]` `component_library` is shared data, so RLS must be read-only for authenticated users. Default grants alone are not enough.

**Suggestions**
- Add an immutable `key`/`slug` unique constraint for `component_library`, and seed with `INSERT ... ON CONFLICT DO UPDATE`.
- Define `project_id REFERENCES projects(id) ON DELETE SET NULL`, plus indexes on `user_id`, `project_id`, and `updated_at`.
- Make `DiagramContent` validate unique node IDs and valid connection endpoints; decide now whether unknown fields are forbidden or explicitly version-gated.

**Risk Assessment**
`MEDIUM` because the structure is good, but the wrong schema choices here would be expensive to unwind later.

## Plan 01-02: Frontend TypeScript Types, Service, Store

**Summary**
Cleanly aligned with current frontend patterns, but it looks under-scoped relative to both the phase goal and the next phase's likely needs.

**Strengths**
- Uses the repo's existing service-factory and Svelte 5 runes store patterns.
- Clear separation of transport types, service methods, and state.

**Concerns**
- `[HIGH]` Only having `list/create/delete` is too thin. A builder feature will need `get(id)` and likely `update(id)` very soon.
- `[MEDIUM]` There is no frontend path for component-library retrieval, even though the phase goal explicitly includes it.
- `[MEDIUM]` Store vs `+page.ts` ownership is unclear. Without a defined hydration/invalidation pattern, stale list state is likely.

**Suggestions**
- Add `get`, `update`, and `listComponents` now, even if the Phase 1 UI only uses a subset.
- Split list/detail types if the backend returns lightweight summaries for list pages and full `content` only on detail fetches.

**Risk Assessment**
`MEDIUM` because the approach is sound, but the contract is incomplete enough that this layer may need rework almost immediately.

## Plan 01-03: Backend API Routes

**Summary**
Directionally correct and probably the most important plan in the phase, but it needs tighter security and API-contract definition before execution.

**Strengths**
- Thin-router/service-layer split matches the current backend well.
- Explicit ownership checks are correctly called out, which matters because the API uses a service-role Supabase client.

**Concerns**
- `[HIGH]` The logo proxy is security-sensitive. The plan does not yet specify domain normalization, content-type/size limits, timeout behavior, redirect handling, or abuse controls.
- `[HIGH]` No `PATCH /diagrams/{id}` route means diagrams are only creatable, not really saveable as editable assets.
- `[MEDIUM]` Component-library response shape is underspecified: flat list vs grouped payload, and all systems vs native-only systems, are both unresolved.
- `[MEDIUM]` Diagram list endpoints should not return full `content` and `thumbnail_base64` by default or list performance will degrade.

**Suggestions**
- Build the proxy only against server-constructed Logo.dev URLs from a normalized domain string; reject full URLs, IPs, private hosts, non-images, and oversized responses.
- Add `PATCH /api/diagrams/{id}` now, and define the component-library contract as either `flat + category` or explicitly grouped, not both.

**Risk Assessment**
`HIGH` because this plan carries the phase's biggest security risk and the biggest chance of forcing near-term API churn.

## Plan 01-04: Frontend UI

**Summary**
Appropriately modest UI scope that fits the existing app shell, but it assumes backend and state contracts that are not fully nailed down yet.

**Strengths**
- Good scope control: nav item, list page, create flow, delete flow, empty state.
- The human verification checkpoint is appropriate for navigation and destructive actions.

**Concerns**
- `[MEDIUM]` The plan does not define how the list stays fresh after create/delete. Loader data plus store mutations needs an explicit sync strategy.
- `[MEDIUM]` There is no "open/view diagram" path, so frontend retrieval remains only partial even if the backend has `GET /diagrams/{id}`.
- `[LOW]` Linked-project selection needs graceful degradation if projects fail to load; create-without-link should still work.

**Suggestions**
- Use a clear invalidation key like `depends('app:diagrams')` and document whether the page or the store is the source of truth.
- Add a minimal detail/open route placeholder now if the backend already supports single-diagram retrieval.

**Risk Assessment**
`MEDIUM` because the UI plan is reasonable, but it depends on contracts that are still a bit underspecified.

## Plan 01-05: Backend Unit Tests + Logo Seed Script

**Summary**
Good inclusion of backend coverage and a dedicated seed script, but this plan mixes deterministic API testing with a network-dependent asset pipeline that needs extra care.

**Strengths**
- Covers the three new backend surfaces instead of leaving Phase 1 untested.
- Keeps logo prefetching separate from the schema migrations, which is the right separation.

**Concerns**
- `[HIGH]` This is labeled TDD, but tests are scheduled after implementation. That means validation, not true TDD.
- `[HIGH]` `seed_logos.py` must never be required for migration success. Missing token, quota exhaustion, or upstream failures cannot block setup.
- `[MEDIUM]` The current mock Supabase test harness does not actually enforce `.eq()` filters, so ownership bugs can slip through if tests rely only on it.
- `[MEDIUM]` Three logo tests are probably insufficient for invalid domain, timeout, upstream 404, content-type rejection, and oversize image cases.

**Suggestions**
- Add at least one stronger ownership test path: either improve the mock builder to honor filters or add a small integration test against real RLS behavior.
- Make `seed_logos.py` opt-in, idempotent, and tolerant of partial failure; test fallback generation and rerun behavior without live Logo.dev calls.

**Risk Assessment**
`MEDIUM-HIGH` because the API test work is straightforward, but the external-logo workflow is operationally fragile unless carefully bounded.

---

## Consensus Summary

### Agreed Strengths
- **Schema versioning** — Both reviewers praise the inclusion of `schema_version` in Phase 1 as forward-thinking data modeling that prevents migration debt
- **Pydantic JSONB validation** — Strong agreement that using nested Pydantic models for JSONB content validation is the right approach
- **Logo caching strategy** — Both see DB-cached base64 logos as superior to live proxying, noting it eliminates rate limit and availability concerns
- **Established patterns** — Universal agreement that cloning existing MIRA patterns (migrations, service layer, store) is the right approach, reducing risk
- **Ownership checks** — Both note user_id filtering and ownership verification as correctly planned for multi-tenant security

### Agreed Concerns
- **Logo proxy SSRF risk (HIGH)** — Both reviewers independently flagged the logo proxy as security-sensitive. Gemini calls out SSRF potential; Codex calls out missing domain normalization, content-type/size limits, and abuse controls. **Action: Add strict domain validation (FQDN regex, no IPs, no private ranges) and content-type/size guards before execution.**
- **Missing PATCH/update endpoint (HIGH)** — Codex flags no `PATCH /api/diagrams/{id}` as a gap that will force immediate rework. Gemini doesn't flag it directly but notes the plan focuses on CRUD — the absence of update is a shared implied concern for a builder tool. **Action: Add update_diagram service + PATCH route in Plan 03; add DiagramUpdate type in Plan 02.**
- **Logo seed script resilience (MEDIUM)** — Both note the seed script must be idempotent and failure-tolerant. Gemini calls for 429 handling; Codex says it must never block setup. **Action: Ensure seed script is opt-in, handles partial failures, and has monogram fallback.**
- **Component library seed data stability (MEDIUM)** — Gemini suggests hardcoded UUIDs for stable references; Codex suggests unique key/slug + upsert-safe INSERT. Both want re-runnable, stable seed data. **Action: Add `ON CONFLICT DO NOTHING` (already present) and consider a `slug` unique key.**

### Divergent Views
- **Soft deletes** — Gemini suggests `deleted_at` for undo capability; Codex does not mention it. *Worth deferring — hard deletes are simpler for v1 and consistent with existing MIRA patterns.*
- **List endpoint payload size** — Codex specifically flags that returning full `content` and `thumbnail_base64` in list queries will degrade performance; Gemini does not raise this. *Worth addressing — add field selection or separate list/detail response models.*
- **Frontend service scope** — Codex calls `list/create/delete` too thin and wants `get/update/listComponents` now; Gemini doesn't flag this. *Worth adding `get` and `update` since the backend already supports them, but `listComponents` can wait for Phase 2 when the configurator actually needs it.*
- **TDD vs validation testing** — Codex notes tests are scheduled after implementation (validation, not TDD). Gemini doesn't raise this. *Acceptable — the plan structure puts tests in a later wave for practical dependency reasons.*
- **JSONB queryability** — Gemini notes JSONB makes cross-diagram queries hard; Codex does not flag this. *Acceptable for v1 — diagrams are individual artifacts, not queryable collections.*
