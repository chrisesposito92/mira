# Testing Patterns

**Analysis Date:** 2026-03-22

---

## Backend (Python)

### Test Framework

**Runner:**
- pytest 8.x with pytest-asyncio 0.24+
- Config: `backend/pyproject.toml` under `[tool.pytest.ini_options]`
- `asyncio_mode = "auto"` — all async test functions run automatically without explicit `@pytest.mark.asyncio` (though some files still include it redundantly)

**Run Commands:**
```bash
cd backend && source .venv/bin/activate
pytest tests/ -v                          # All tests
pytest -m "not integration"               # Unit tests only (no Supabase needed)
pytest -m "not integration and not eval_live"  # CI subset
pytest tests/test_health.py               # Single file
pytest tests/ -k "TestProductValidation"  # Single class
```

**Assertion Library:**
- Python's built-in `assert` — pytest rewrites for readable output

### Test File Organization

**Location:**
- All unit and integration tests in `backend/tests/`
- Evaluation tests in `backend/evals/` (separate testpath, different markers)
- One test file per module/area: `test_validation_rules.py`, `test_api_generated_objects.py`, `test_plan_pricing_graph.py`

**Naming:**
- Files: `test_{subject}.py`
- Classes: `Test{Subject}` — e.g., `TestProductValidation`, `TestM3terClientTokenCaching`
- Functions: `test_{what_it_does}` — e.g., `test_valid_product_passes`, `test_fresh_token_fetched`

### pytest Markers

Defined in `backend/pyproject.toml`:

| Marker | Meaning |
|--------|---------|
| `integration` | Requires running Supabase (Docker). Set via `pytestmark` at module level. |
| `eval` | All eval tests (structural/schema/completeness). |
| `eval_live` | Eval tests requiring real LLM API calls. Excluded from CI. |

**Usage patterns:**
```python
# Module-level marker (integration tests)
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

# Per-test marker (async node tests)
@pytest.mark.asyncio
async def test_generates_product_list(self, ...):
    ...

# Eval tests (parametrized)
@pytest.mark.eval
@pytest.mark.eval_live
@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=lambda e: e.name)
async def test_wf1_quality(example, eval_model_id):
    ...
```

### Test Structure

**Class-based grouping (used consistently throughout):**
```python
class TestProductValidation:
    def _valid_meter(self) -> dict:
        """Helper that builds a minimal valid entity dict."""
        return {"name": "...", "code": "...", "dataFields": [...]}

    def test_valid_product_passes(self):
        errors = validate_entity(EntityType.product, {"name": "API Gateway", "code": "api_gateway"})
        assert len(errors) == 0

    def test_missing_name_fails(self):
        errors = validate_entity(EntityType.product, {"code": "api_gateway"})
        error_fields = [e.field for e in errors]
        assert "name" in error_fields
```

**Setup/Teardown:**
- `@pytest.fixture(scope="session")` for one-time migration application (`apply_migrations`)
- `@pytest_asyncio.fixture` for per-test DB connections with transaction rollback (`db_conn`)
- `@pytest.fixture(autouse=True)` for resetting class-level state (e.g., `clear_cache`)
- No `setUp`/`tearDown` methods — pytest fixtures only

### Fixtures (`backend/tests/conftest.py`)

**Core fixtures available to all tests:**

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `apply_migrations` | session | Runs all SQL migrations once |
| `db_conn` | function | asyncpg connection with automatic transaction rollback |
| `mock_supabase` | function | `MagicMock` Supabase client with configurable `_table_data` dict |
| `authed_client` | function | `TestClient(app)` with auth + Supabase DI overridden |
| `mock_config` | function | Minimal `RunnableConfig` dict (`{}`) for node tests |
| `mock_user_id` | function | Fixed UUID constant `MOCK_USER_ID` |
| `fernet_key` | function | Patches `ENCRYPTION_KEY` env var and `settings` for encryption tests |

**MockPostgrestBuilder — chainable Supabase mock:**
```python
# Configure table data before test
mock_supabase._table_data["use_cases"] = [{"id": ucid, "projects": {"user_id": str(MOCK_USER_ID)}}]
mock_supabase._table_data["generated_objects"] = [_object_row(use_case_id=ucid)]

# Supports full Supabase query chain:
# supabase.table("use_cases").select("*").eq("id", ucid).execute()
```

**TestClient without context manager (critical):**
```python
# CORRECT — avoids triggering lifespan (get_db_pool requires real Postgres)
yield TestClient(app, raise_server_exceptions=False)

# WRONG — triggers lifespan and fails without DB
with TestClient(app) as client:
    ...
```

**DI override cleanup with try/finally:**
```python
app.dependency_overrides[get_current_user] = lambda: MOCK_USER_ID
app.dependency_overrides[get_supabase] = lambda: mock_supabase
try:
    yield TestClient(app, raise_server_exceptions=False)
finally:
    app.dependency_overrides.clear()  # Prevents leaked overrides between tests
```

### Mocking Patterns

**LLM mocking (agent node tests):**
```python
def _make_llm_response(content: str | dict | list) -> MagicMock:
    response = MagicMock()
    response.content = json.dumps(content) if isinstance(content, dict | list) else content
    return response

@patch("app.agents.nodes.generation.get_llm")
async def test_generates_product_list(self, mock_get_llm, base_state, mock_config):
    mock_llm_instance = AsyncMock()
    mock_llm_instance.ainvoke.return_value = _make_llm_response([...])
    mock_get_llm.return_value = mock_llm_instance
```

**Patching at import site (not definition site):**
```python
# Patch where it's imported/used, not where it's defined
@patch("app.agents.nodes.analysis.rag_retrieve", new_callable=AsyncMock)
@patch("app.agents.nodes.analysis.get_llm")
@patch("app.agents.nodes.analysis.get_supabase_client")
```

**WebSocket test patching:**
```python
def _ws_patches(mock_supabase):
    return (
        patch("app.api.ws.verify_token", return_value={"sub": str(MOCK_USER_ID)}),
        patch("app.api.ws.get_supabase_client", return_value=mock_supabase),
    )

with p_token, p_supabase:
    with authed_client.websocket_connect(f"/ws/documents/{pid}?token=valid-token") as ws:
        msg = ws.receive_json()
```

**Row builder helpers (repeated pattern across API test files):**
```python
def _use_case_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "project_id": str(uuid4()),
        "projects": {"user_id": str(MOCK_USER_ID)},  # Join data required for ownership checks
    }
    defaults.update(overrides)
    return defaults
```
Note: mock rows for ownership checks **must include join data** (e.g., `use_cases.projects.user_id`) or queries return 404.

**m3ter client mocking (HTTP-level):**
```python
with patch.object(client._session, "post", new=AsyncMock(return_value=mock_response)):
    ...
```

### Fixtures and Factories

**Test data builders:** Local `_*_row()` helper functions per test file — not a shared factory module.

**Base state for agent tests:**
```python
@pytest.fixture
def base_state() -> dict:
    return {
        "use_case_id": "uc-111",
        "project_id": "proj-222",
        "model_id": "claude-sonnet-4-6",
        "user_id": "user-333",
    }
```

**Integration test user creation:**
- Module-level `_shared_user` dict, lazily initialized via `_ensure_test_user()`
- Uses Supabase admin API to bypass email rate limits

### Test Types

**Unit Tests (majority of `backend/tests/`):**
- Validation rules: `test_validation_rules.py`, `test_validation_plan_pricing.py`, `test_validation_compound_agg.py`, `test_account_validation.py`
- Agent nodes: `test_nodes.py`, `test_plan_pricing_graph.py`, `test_account_setup_graph.py`, `test_usage_submission_graph.py`
- API routes: `test_api_generated_objects.py`, `test_api_org_connections.py`, `test_api_projects.py`, `test_api_use_cases.py`
- Service logic: `test_push.py`, `test_encryption.py`, `test_llm_factory.py`
- Memory modules: `test_memory.py`, `test_memory_decisions.py`, `test_memory_rag.py`

**Integration Tests (`@pytest.mark.integration`):**
- `test_auth.py` — GoTRUE signup/login flows
- `test_migrations.py` — SQL migration application
- `test_rls.py` — Row-level security policies
- `test_pgvector.py` — pgvector embedding storage

**Evaluation Tests (`backend/evals/`, `@pytest.mark.eval_live`):**
- `test_eval_wf1.py`, `test_eval_wf2.py`, `test_eval_wf3.py` — per-workflow quality scoring
- `test_eval_chain.py` — full WF1→WF2→WF3 chain evaluation
- Use `eval_patches` context manager to mock Supabase/RAG while keeping real LLM calls
- Minimum quality thresholds enforced as assertions: `assert composite.score >= 0.50`

### Coverage

**Requirements:** No coverage targets enforced. No `--cov` flag in standard test commands.

**CI exclusions:** `pytest -m "not integration and not eval_live"` — skips DB-dependent and LLM-dependent tests.

---

## Frontend (TypeScript / Svelte)

### Test Framework

**Runner:**
- Vitest 4.x
- Config: `frontend/vitest.config.ts`
- Environment: `jsdom`
- Setup file: `frontend/src/tests/setup.ts` (loads `@testing-library/jest-dom/vitest` matchers)

**Run Commands:**
```bash
cd frontend
npm run test          # vitest run (single pass)
npm run test:watch    # vitest (watch mode)
```

**No coverage command configured.** Coverage not tracked.

### Test File Organization

**Location:** Co-located with source files in `src/`
- Store tests: `src/lib/stores/*.test.ts` or `*.svelte.test.ts`
- Service tests: `src/lib/services/*.test.ts`
- Component tests: `src/lib/components/**/*.test.ts` or `*.svelte.test.ts`
- Utility tests: `src/lib/utils.test.ts`

**Naming:**
- `{filename}.test.ts` for plain TS modules
- `{ComponentName}.svelte.test.ts` for Svelte component tests
- `{storeName}.svelte.test.ts` for runes-based store tests

**Included glob:** `src/**/*.test.ts` (configured in `vitest.config.ts`)

### Test Structure

**Vitest describe/it pattern:**
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('ObjectsStore', () => {
  it('initializes with empty state', () => {
    expect(store.objects).toEqual([]);
  });

  it('loadObjects populates objects', async () => {
    const service = mockObjectService();
    await store.loadObjects(service, 'uc-1');
    expect(store.objects).toHaveLength(3);
    expect(service.listObjects).toHaveBeenCalledWith('uc-1');
  });
});
```

**Svelte 5 runes store tests — dynamic import pattern:**
```typescript
// Required for Svelte 5 runes module — NOT static import
let store: Awaited<typeof import('./objects.svelte.js')>['objectsStore'];

beforeEach(async () => {
  const mod = await import('./objects.svelte.js');
  store = mod.objectsStore;
  store.clear();  // Reset singleton state before each test
});
```

**Svelte component tests (Testing Library):**
```typescript
import { render, screen, fireEvent } from '@testing-library/svelte';
import ProjectCard from './ProjectCard.svelte';

render(ProjectCard, { props: { project: baseProject } });
expect(screen.getAllByText('Test Project').length).toBeGreaterThanOrEqual(1);
```
Note: Use `getAllByText` (not `getByText`) for Svelte components — elements may appear in multiple DOM locations (e.g., title + aria-label).

### Mocking

**Framework:** Vitest's built-in `vi` mock utilities

**Fetch mocking (API client tests):**
```typescript
const spy = vi
  .spyOn(globalThis, 'fetch')
  .mockResolvedValue(new Response(JSON.stringify({ id: '1' }), { status: 200 }));
```

**Service mocking (store tests):**
```typescript
function mockObjectService(overrides = {}): GeneratedObjectService {
  return {
    listObjects: vi.fn().mockResolvedValue([...]),
    updateObject: vi.fn().mockResolvedValue(makeMockObject({ id: 'obj-1', name: 'Updated' })),
    // ...all interface methods...
    ...overrides,  // Allow selective override per test
  };
}
```

**Supabase client mocking (auth tests):**
```typescript
function mockSupabase(token = 'test-token') {
  return {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: token } },
      }),
    },
  } as any;
}
```

**Cleanup:**
```typescript
beforeEach(() => {
  vi.restoreAllMocks();  // Clears spies; used in ApiClient tests
});
```

**What to Mock:**
- `fetch` (via `vi.spyOn(globalThis, 'fetch')`) in service unit tests
- All external service dependencies injected into stores
- Supabase auth session for client tests

**What NOT to Mock:**
- The store itself when testing it — use actual store with `clear()` reset
- The `cn()` utility — tested directly against real implementation

### Fixtures and Factories

**Object builder functions (local to each test file):**
```typescript
function makeMockObject(
  overrides: Partial<GeneratedObject> = {},
): GeneratedObject {
  return {
    id: 'obj-1',
    use_case_id: 'uc-1',
    entity_type: 'product',
    // ...all required fields with defaults...
    ...overrides,
  };
}
```

**Base data constants:**
```typescript
const baseProject = {
  id: '1',
  user_id: 'u1',
  name: 'Test Project',
  // ...all required fields...
};
```

**Location:** Defined locally at the top of each test file — no shared factory module.

### Test Types

**Unit tests for services:**
- `src/lib/services/api.test.ts` — `ApiClient` HTTP methods, error handling, auth headers
- `src/lib/services/generated-objects.test.ts` — `GeneratedObjectService` URL construction
- `src/lib/services/workflow.test.ts` — `WorkflowService` endpoint calls
- `src/lib/services/projects.test.ts` — `ProjectService` CRUD calls

**Unit tests for stores:**
- `src/lib/stores/objects.svelte.test.ts` — state management, filtering, tree ordering, CRUD ops, push state
- `src/lib/stores/workflow.svelte.test.ts` — WebSocket message handling, HITL decision accumulation
- `src/lib/stores/project.svelte.test.ts` — project/use-case CRUD, document management
- `src/lib/stores/auth.svelte.test.ts` — session/user/profile set/clear
- `src/lib/stores/org-connections.svelte.test.ts` — connection CRUD and testing

**Component tests:**
- `src/lib/components/project/ProjectCard.svelte.test.ts` — rendering, formatted date, button role
- `src/lib/components/project/FileUpload.svelte.test.ts` — drop zone, document list, uploading state
- `src/lib/components/project/UploadProgressBar.svelte.test.ts` — progress bar phases
- `src/lib/components/control-panel/UseCaseMetadataPanel.test.ts` — metadata display
- `src/lib/components/project/use-case-generator.test.ts` — generator dialog logic

**Utility tests:**
- `src/lib/utils.test.ts` — `cn()` class merging, Tailwind deduplication

### Async Testing

```typescript
it('loadObjects populates objects', async () => {
  const service = mockObjectService();
  await store.loadObjects(service, 'uc-1');
  expect(store.objects).toHaveLength(3);
});
```
Async tests use standard `async/await` — no special configuration needed with Vitest.

### Error Testing

```typescript
it('loadObjects sets error on failure', async () => {
  const service = mockObjectService({
    listObjects: vi.fn().mockRejectedValue(new Error('Network error')),
  });
  await store.loadObjects(service, 'uc-1');
  expect(store.error).toBe('Network error');
  expect(store.objects).toEqual([]);
});

it('throws ApiError on non-ok response', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 }),
  );
  try {
    await client.get('/api/projects/bad');
    expect.unreachable('Should have thrown');
  } catch (e) {
    expect(e).toBeInstanceOf(ApiError);
    expect((e as ApiError).status).toBe(404);
  }
});
```

### Coverage

**Requirements:** Not enforced. No coverage configuration present.

**No E2E tests configured.** The `frontend/tests/` directory exists but is empty. All tests are unit/component level via Vitest + jsdom.

---

*Testing analysis: 2026-03-22*
