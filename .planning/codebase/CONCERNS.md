# Codebase Concerns

**Analysis Date:** 2026-03-22

## Tech Debt

**Dual Database Connection Pools:**
- Issue: Two separate connection pools exist to the same Postgres database — an `asyncpg.Pool` in `app/db/client.py` (`_db_pool`, min=2/max=10) and a `psycopg_pool.AsyncConnectionPool` in `app/agents/checkpointer.py` (`_psycopg_pool`, min=2/max=15). This doubles connection overhead (up to 25 idle connections).
- Files: `backend/app/db/client.py`, `backend/app/agents/checkpointer.py`
- Impact: Wastes Supabase connection quota, two pools to shut down on lifespan.
- Fix approach: Consolidate — use psycopg for everything (LangGraph prefers psycopg anyway) or keep asyncpg for RAG/raw SQL and wire LangGraph checkpointer to use the same asyncpg pool.

**Dependency Version Floor Too Low:**
- Issue: `pyproject.toml` specifies `"langgraph>=0.2.0"` and `"langchain>=0.3.0"`. The code explicitly handles both LangGraph 0.x (raises `GraphInterrupt`) and 1.x (returns normally on interrupt) behavior with dual code paths in `ws.py` and `workflow_service.py`. The 0.x compat code is dead weight.
- Files: `backend/pyproject.toml`, `backend/app/api/ws.py`, `backend/app/services/workflow_service.py`
- Impact: Adds cognitive overhead, dual code paths in critical hot paths.
- Fix approach: Pin floor to `langgraph>=1.0.0`, remove the `except GraphInterrupt: pass` compatibility shunts.

**Unbounded `SELECT *` Queries:**
- Issue: Fourteen service-layer queries use `.select("*")` with no column projection. Most critical: `push_service.py` fetches all `generated_objects` columns including the full JSON `data` blob for entire use cases when computing push status or resolving references.
- Files: `backend/app/services/push_service.py` (lines 75, 123, 169, 220), `backend/app/services/generated_object_service.py`, `backend/app/services/project_service.py`, `backend/app/services/workflow_service.py`, and others.
- Impact: Over-fetches large `data` JSON blobs unnecessarily; degrades on large use cases.
- Fix approach: Project only needed columns per query (e.g., `select("id, entity_type, status, m3ter_id, data")` for push engine, `select("id, status")` for status counts).

**`compound_aggregation` Entity Incompleteness:**
- Issue: CompoundAggregation is generated (WF1), validated, and approved but has no push mapper or m3ter client method. It is explicitly excluded from `PUSH_ORDER` in `entities.py`. The frontend also excludes it from `CreateObjectDialog`. There is no user-visible indication that these entities will never be pushed.
- Files: `backend/app/m3ter/entities.py` (PUSH_ORDER comment), `backend/app/m3ter/mapper.py` (no compound_aggregation entry), `frontend/src/lib/components/control-panel/CreateObjectDialog.svelte`
- Impact: Users approve compound aggregations and they silently stay in the DB, never reaching m3ter.
- Fix approach: Either implement the m3ter API call for compound aggregations or surface a clear UI warning that compound aggregations are advisory-only and won't be pushed.

**N+1 DB Updates in Approval Node:**
- Issue: In `approve_entities()`, each decision in the loop issues a separate `supabase.table("generated_objects").update(...).execute()` call. For a batch of 20 entities, this is 20+ sequential DB round-trips in addition to the initial bulk upsert.
- Files: `backend/app/agents/nodes/approval.py` (lines 198–222, 306–310)
- Impact: Adds 100–500ms latency per approval round-trip (sequential synchronous Supabase client calls).
- Fix approach: Collect decisions into status buckets (approve/reject/edit), then issue batched updates using `.in_("id", [ids]).update(...)` where data payloads are homogeneous; fall back to individual calls only for edits with unique data payloads.

**CORS Origins Not Configurable for Production:**
- Issue: The default `cors_origins` in `config.py` is hardcoded to `["http://localhost:5173"]`. There is no documented env var to override this for production deployments. The config accepts a list but Pydantic settings parsing from env vars requires a JSON-encoded list string.
- Files: `backend/app/config.py` (line 12), `backend/app/main.py` (line 35)
- Impact: Production deployments require code changes or non-obvious env var formatting to set correct CORS origins.
- Fix approach: Document `CORS_ORIGINS='["https://app.example.com"]'` in `.env.example`, or switch to a comma-separated string that's parsed in the settings model.

---

## Security Considerations

**JWT Passed as WebSocket Query Parameter:**
- Risk: All four WebSocket endpoints (`/ws/workflows/{id}`, `/ws/push/{id}`, `/ws/documents/{id}`, `/ws/generate/{id}`) authenticate via a `?token=<jwt>` query parameter. Query params appear in server access logs, browser history, and proxy logs — the JWT is leaked at every hop.
- Files: `backend/app/api/ws.py` (`_authenticate_ws` function, line 31), `frontend/src/lib/services/websocket.ts` (line 55)
- Current mitigation: None — token is in the URL.
- Recommendations: Use the WebSocket subprotocol header or send the token as the first client message after connection. Most browsers support `Sec-WebSocket-Protocol` header for this purpose.

**Service Role Key Used Everywhere — RLS Bypassed:**
- Risk: `get_supabase_client()` always uses the service role key, which bypasses Row-Level Security on every DB operation. All authorization is enforced purely in Python application code. If any route handler is misconfigured or skips the ownership check, data from other users is accessible.
- Files: `backend/app/db/client.py` (line 15–22). `get_supabase_anon_client()` exists but is never called from any application code — only exported.
- Current mitigation: Manual ownership checks in every service function (join-based pattern: `projects!inner(user_id)`).
- Recommendations: Use the service role key only for admin/background operations. For user-facing queries, use the anon client with RLS or pass user JWTs through the Supabase client.

**Encryption Key Weakness — No Key Rotation Support:**
- Risk: m3ter OAuth credentials (client_id, client_secret) are encrypted with a single Fernet key stored in `ENCRYPTION_KEY`. There is no key rotation mechanism: if the key is rotated, all stored credentials become undecryptable.
- Files: `backend/app/m3ter/encryption.py`, `backend/app/services/org_connection_service.py`
- Current mitigation: Single Fernet key, no versioning.
- Recommendations: Implement key versioning (store key ID alongside ciphertext) and a re-encryption migration path.

**LangSmith Traces May Contain Sensitive Data:**
- Risk: When `LANGSMITH_TRACING=true`, all LLM inputs/outputs (including full use case context, entity data, m3ter org details injected into prompts) are sent to LangSmith. This includes potentially sensitive billing configuration data.
- Files: `backend/app/config.py` (lines 62–68), `backend/app/agents/graphs/` (all graph builders pass metadata/tags)
- Current mitigation: Feature is opt-in via env var.
- Recommendations: Document data sensitivity implications. Consider using LangSmith's data masking features or a self-hosted LangSmith instance for production.

---

## Performance Bottlenecks

**Sequential Supabase Client — Synchronous I/O in Async Handlers:**
- Problem: The `supabase-py` client is synchronous. Every `supabase.table(...).execute()` call blocks the asyncio event loop. In `approve_entities()` alone there are 3–25 blocking calls per invocation. FastAPI and LangGraph are fully async, so these calls serialize what could run concurrently.
- Files: `backend/app/agents/nodes/approval.py`, `backend/app/services/` (all service files)
- Cause: `supabase-py` 2.x doesn't have true async support — the async methods are thin wrappers around sync HTTP.
- Improvement path: Use `asyncio.to_thread()` for Supabase calls in hot paths, or migrate to direct asyncpg queries for the approval node's batch write operations where performance matters most.

**Single-Use Case Fetches All Generated Objects:**
- Problem: In `push_service.push_use_case_objects()`, the query `SELECT * FROM generated_objects WHERE use_case_id = $1` fetches ALL objects for the use case in one go, including the full `data` JSON blob. A use case with 50+ objects (each with a potentially large JSON payload) sends a large result set over the wire.
- Files: `backend/app/services/push_service.py` (line 169)
- Cause: No server-side filtering beyond use_case_id; `SELECT *` retrieves `data` blob unconditionally.
- Improvement path: For status computation, project only `id, status, entity_type`. Fetch full `data` only for objects being actively pushed.

**RAG Retrieval Fetches Twice Per Generation Step (WF1 Nodes):**
- Problem: WF1 generation nodes (`generate_products`, `generate_meters`, `generate_aggregations`, `generate_compound_aggregations`) each call `rag_retrieve()` independently. WF1 runs all four in sequence; each makes an OpenAI embedding API call plus a pgvector query.
- Files: `backend/app/agents/nodes/generation.py` (each generate_* function), `backend/app/agents/tools/rag_tool.py`
- Cause: RAG context is fetched per generation step rather than once at analysis time and shared.
- Improvement path: Fetch RAG context once in the analysis node and store in state; generation nodes read from state rather than calling the retriever.

**Memory Store Searches Scale Linearly:**
- Problem: `memory_rag.py` calls `store.asearch(namespace, limit=500)` — fetching up to 500 items to find a single chunk's score. As RAG feedback accumulates this scan will slow down.
- Files: `backend/app/agents/memory_rag.py` (line 132)
- Cause: LangGraph's `AsyncPostgresStore` doesn't support direct key lookups with `aget`; `asearch` is used as a workaround.
- Improvement path: Use `store.aget(namespace, key)` directly for exact-key lookups (already available in LangGraph Store API) instead of scanning all 500 items.

---

## Fragile Areas

**LangGraph `interrupt()` Resume Race on Reconnect:**
- Files: `backend/app/api/ws.py` (lines 219–239), `frontend/src/lib/stores/workflow.svelte.ts` (`restoredFromHistory` flag)
- Why fragile: When a client reconnects mid-interrupt, the backend sends the current interrupt payload and the frontend must distinguish a "replay" from a new interrupt using `restoredFromHistory = true`. If the connection drops during the window between sending the interrupt and setting `restoredFromHistory`, the client may display a duplicate entity card.
- Safe modification: Always set `restoredFromHistory = true` before establishing the WS connection when restoring from an interrupted state.
- Test coverage: No test for the reconnect+duplicate-message scenario.

**`_question_cache` Module-Level Dict in Two Files:**
- Files: `backend/app/agents/nodes/clarification.py` (line 21), `backend/app/agents/nodes/use_case_clarify.py` (line 18)
- Why fragile: Both files maintain separate module-level `_question_cache` dicts keyed by `thread_id`. If a worker process restarts mid-interrupt (e.g., uvicorn reload, Vercel function cold start), the cache is lost and the next LangGraph node re-execution generates fresh questions — but the user's interrupt payload in the DB still references the old questions. The `cleanup_question_cache()` function is called on WS close but not on process restart.
- Safe modification: Store questions in LangGraph state (they're already in `clarification_questions` state key after interrupt) rather than a process-local dict.
- Test coverage: No test for the restart-mid-interrupt scenario.

**Uploaded Files on Local Disk — Not Deployment-Safe:**
- Files: `backend/app/config.py` (line 55: `upload_dir: str = "uploads"`), `backend/app/services/document_service.py` (line 60)
- Why fragile: Uploaded documents are stored at `backend/uploads/<project_id>/<doc_id>_<filename>` on the local filesystem. The `backend/uploads/` directory currently contains 77+ subdirectories of live data committed/present on disk. On Vercel (serverless/ephemeral), the filesystem is read-only at deploy time and write-ephemeral at runtime — files written during one invocation disappear on the next cold start.
- Safe modification: Files deleted via `delete_document` are cleaned up (`Path.unlink(missing_ok=True)`) but orphaned files from failed uploads are never cleaned up.
- Test coverage: No test for disk cleanup on delete failure.

**Approval Node Idempotency via uuid5 — Collision Potential:**
- Files: `backend/app/agents/nodes/approval.py` (line 155): `obj_id = str(uuid5(NAMESPACE_DNS, f"{thread_id}:{entity_type}:{i}"))`
- Why fragile: Entity IDs are deterministic based on position index `i`. If a workflow is resumed and the LLM re-generates a different number of entities for the same step, the index-based IDs shift — the upsert correctly handles this for new entities but historical DB rows for the previous run's indices are left as orphaned `draft` rows.
- Safe modification: The upsert handles duplicate inserts correctly, but the orphaned-draft-rows issue means `list_objects` will return stale draft rows from prior aborted runs.

**`document_processing_registry.py` — In-Process Only:**
- Files: `backend/app/services/document_processing_registry.py`
- Why fragile: The `_listeners` dict is module-level and in-process. If the backend runs with multiple workers (`uvicorn --workers N`), the WebSocket connection for document progress may land on a different worker than the one processing the document. The `doc_processing_*` events will never reach the client.
- Safe modification: Safe with a single worker (current default `uvicorn --reload`). Breaking if deployed with multiple workers.
- Test coverage: Not tested for multi-worker scenario.

---

## Scaling Limits

**LangGraph Checkpoint Postgres — Unbounded State Growth:**
- Current capacity: The `checkpoints` table (LangGraph-managed) stores every workflow state snapshot with no TTL or cleanup policy.
- Limit: As workflow count grows, checkpoint table grows unboundedly. LangGraph's `AsyncPostgresStore` also stores memory entries with no eviction.
- Scaling path: Add a periodic cleanup job that deletes checkpoint rows for workflows with `status IN ('completed', 'failed')` older than N days.

**WebSocket Connection Count Per Worker:**
- Current capacity: FastAPI/Starlette handles all WebSocket connections in a single asyncio event loop per worker. With 4 WebSocket endpoint types and concurrent users, connection count is bounded only by OS limits.
- Limit: Workflow WebSockets are long-lived (blocked on LLM calls for minutes). Under concurrent usage, the single asyncio thread becomes saturated.
- Scaling path: Horizontal scaling requires solving the `document_processing_registry.py` and `_question_cache` in-process state issues first (see Fragile Areas).

---

## Dependencies at Risk

**`psycopg_pool` (psycopg3) vs `asyncpg` Dual Dependency:**
- Risk: The project depends on both `asyncpg` (for RAG raw SQL and DB pool) and `psycopg` (for LangGraph's `AsyncPostgresSaver`/`AsyncPostgresStore`). These are two Postgres client libraries with different APIs maintained independently.
- Impact: Double maintenance surface; version conflicts possible with future Postgres driver updates.
- Migration plan: Consolidate on one library. LangGraph now supports asyncpg adapters; alternatively migrate RAG queries to psycopg.

**LangGraph Minimum Version `>=0.2.0` — Too Permissive:**
- Risk: LangGraph had significant API changes between 0.x and 1.x (interrupt behavior, Store API). The `>=0.2.0` floor allows installing a 0.x version that breaks the codebase.
- Impact: A fresh install on a system with dependency caching could pull 0.x.
- Migration plan: Pin to `>=1.0.0` or lock to a specific version in `requirements.txt`/`uv.lock`.

**Playwright for Scraper — Large Unused Runtime Dependency:**
- Risk: `playwright>=1.49.0` is listed as a production dependency in `pyproject.toml` but is only used in the scraper script (`scripts/scrape_m3ter_docs.py`), which is a one-time developer operation. Playwright installs browser binaries (~300 MB) on `pip install`.
- Impact: Bloated production Docker images; unnecessary attack surface.
- Migration plan: Move Playwright to `[project.optional-dependencies]` scraper group or use httpx-only scraping (the current scraper uses httpx + beautifulsoup4 anyway — Playwright may be unused).

---

## Missing Critical Features

**No File Storage Migration Path for Production:**
- Problem: Uploaded documents are written to local disk (`uploads/`). There is no S3/GCS/Supabase Storage integration. The current code cannot run on any ephemeral compute platform (Vercel, Cloud Run, etc.) without data loss.
- Blocks: Cannot deploy to serverless/containerized environments where filesystem is ephemeral.

**No LangGraph Checkpoint Cleanup:**
- Problem: No background job or API endpoint exists to clean up completed/failed workflow checkpoints from the `checkpoints` table (LangGraph-managed Postgres tables).
- Blocks: Long-term database bloat; no operator tooling to reclaim disk space.

**No Rate Limiting on LLM-Backed Endpoints:**
- Problem: The workflow start endpoint (`POST /api/use-cases/{id}/workflows/start`) and use case generator (`/ws/generate/{id}`) make LLM API calls with no request rate limiting per user. A single user can trigger unlimited concurrent LLM calls.
- Blocks: Cost control; protection against accidental runaway usage.

---

## Test Coverage Gaps

**WebSocket Endpoints Not Tested:**
- What's not tested: The four WebSocket handlers in `ws.py` (`workflow_ws`, `push_ws`, `document_ws`, `generate_ws`) have zero test coverage. Authentication, ownership checks, message routing, and error handling paths are untested.
- Files: `backend/app/api/ws.py`
- Risk: Regressions in WS protocol handling go undetected; reconnect logic, mid-session disconnect, and invalid message handling are production-only paths.
- Priority: High

**Approval Node DB Behavior Not Tested:**
- What's not tested: The `approve_entities` function's post-interrupt DB operations (upsert, per-decision updates, undecided auto-promotion) are not tested in the unit test suite. `test_nodes.py` mocks the interrupt but doesn't verify the resulting DB state.
- Files: `backend/app/agents/nodes/approval.py`, `backend/tests/test_nodes.py`
- Risk: Silent data inconsistency between approved state and DB rows.
- Priority: High

**Push Engine Reference Resolution Not Fully Tested:**
- What's not tested: Cross-entity reference resolution failures (e.g., pricing entity with unresolvable planId, entity pushed out of order) are not covered. `test_push.py` covers the happy path but not `ReferenceResolutionError` scenarios at the engine level.
- Files: `backend/app/m3ter/entities.py`, `backend/tests/test_push.py`
- Risk: Reference errors surface only in production against real m3ter API.
- Priority: Medium

**Frontend Workflow Store WebSocket Reconnect Not Tested:**
- What's not tested: The `WebSocketClient` reconnect logic (exponential backoff, max attempts, `intentionalClose` flag) and the `restoredFromHistory` flag behavior in `WorkflowStore` are not covered by `workflow.svelte.test.ts`.
- Files: `frontend/src/lib/services/websocket.ts`, `frontend/src/lib/stores/workflow.svelte.test.ts`
- Risk: Reconnect regressions leave users with a broken chat UI after network blips.
- Priority: Medium

**Integration Tests Require Live Supabase:**
- What's not tested: RLS policy tests (`test_rls.py`), migration tests (`test_migrations.py`), and pgvector tests (`test_pgvector.py`) are all marked `integration` and excluded from CI (`pytest -m "not integration and not eval_live"`). RLS policies are never validated in the automated pipeline.
- Files: `backend/tests/test_rls.py`, `.github/workflows/ci.yml` (line 71)
- Risk: RLS regressions (data leaks between users) are only caught if a developer runs integration tests manually with a local Supabase Docker instance.
- Priority: High

---

*Concerns audit: 2026-03-22*
