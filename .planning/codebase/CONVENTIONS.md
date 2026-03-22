# Coding Conventions

**Analysis Date:** 2026-03-22

---

## Python (backend)

### Naming Patterns

**Files:**
- Module names use `snake_case` throughout: `project_service.py`, `llm_factory.py`, `cross_entity.py`
- Test files are prefixed `test_`: `test_api_generated_objects.py`, `test_plan_pricing_graph.py`
- Node modules are short verbs or compound nouns: `generation.py`, `validation.py`, `load_approved.py`

**Functions:**
- All public functions use `snake_case`: `validate_entity()`, `create_project()`, `get_current_user()`
- Private helpers use leading underscore: `_format_clarification_answers()`, `_make_llm_response()`, `_build_graph()`
- Async functions always marked `async def`; no sync wrappers around async logic

**Variables:**
- `snake_case` throughout: `use_case_id`, `model_id`, `plan_template_errors`
- Module-level constants use `SCREAMING_SNAKE_CASE`: `CODE_PATTERN`, `VALID_CATEGORIES`, `MOCK_USER_ID`
- Module-level registries also use uppercase: `MODEL_REGISTRY`, `PUSH_ORDER`

**Classes:**
- `PascalCase`: `ProjectCreate`, `MockPostgrestBuilder`, `M3terClient`, `ValidationError`
- Pydantic schemas always follow `{Entity}{Create|Update|Response}` pattern

**Types:**
- TypedDicts use `PascalCase` and declare `total=False` when all fields optional: `WorkflowState`
- Enum fields defined in `app/schemas/common.py` as `EntityType`, accessed as `EntityType.product`

### Code Style

**Formatting / Linting:**
- Ruff handles both linting and formatting (configured in `backend/pyproject.toml`)
- Line length: **100 characters**
- Target Python version: **3.12**
- Active rule sets: `E` (pycodestyle errors), `F` (pyflakes), `I` (isort), `N` (naming), `W` (warnings), `UP` (pyupgrade)

**Specific enforced rules:**
- `from datetime import UTC` — never `timezone.utc` (UP017)
- `str | None` union syntax, not `Optional[str]` (UP006/UP007)
- `list[dict]` lowercase generics, not `List[Dict]` (UP006)

### Import Organization

**Order (isort, enforced by ruff `I` rule):**
1. Standard library (`from collections.abc import ...`, `from uuid import UUID`)
2. Third-party (`from fastapi import ...`, `import pytest`)
3. Local app (`from app.schemas.projects import ...`, `from app.agents.llm_factory import get_llm`)

**Pattern:**
- Local imports use absolute paths from `app.*` root — no relative imports
- `from app.dependencies import get_current_user, get_supabase` is the canonical DI import

### Module Design

**API routes (`backend/app/api/`):**
- One file per resource: `projects.py`, `use_cases.py`, `generated_objects.py`
- Always define `router = APIRouter(prefix="/api/...", tags=[...])`
- Route handlers are thin: extract params, call service, return result
- All route handlers are `async def` with type annotations including return type

**Service layer (`backend/app/services/`):**
- Service functions are plain synchronous functions (Supabase SDK is sync)
- Signature convention: `func(supabase: Client, user_id: UUID, ...) -> dict | list[dict]`
- Ownership checks before any mutation — raise `HTTPException(404)` if not found
- Use `data.model_dump(exclude_unset=True)` for partial updates

**Validation layer (`backend/app/validation/`):**
- Per-entity modules in `validation/rules/` each expose a single `validate(data: dict) -> list[ValidationError]` function
- Shared field validators in `validation/common.py`: `validate_name()`, `validate_code()`, `validate_non_negative()`
- `ValidationError` is a `@dataclass` with `field`, `message`, `severity` ("error" | "warning")
- Dispatch goes through `validate_entity(entity_type, data)` in `validation/engine.py`

**Agent nodes (`backend/app/agents/nodes/`):**
- Each node is an `async def` function: `async def generate_products(state: WorkflowState, config: RunnableConfig) -> dict`
- Nodes return partial state dicts — only the keys they update
- LLM calls follow: `llm = get_llm(model_id); response = await llm.ainvoke([SystemMessage(...), HumanMessage(...)])`
- Parse LLM output with `parse_entity_list(content)` and `extract_llm_text()`
- Memory operations are always wrapped in `try/except` — memory is additive, never required

### Error Handling

**Pattern:**
- Service layer raises `HTTPException` directly: `raise HTTPException(status_code=404, detail="Project not found")`
- Custom `AuthError` exception in `app/auth/jwt.py` — handled globally in `app/main.py` via `@app.exception_handler(AuthError)`
- LangGraph node errors set `state["error"]` and `state["current_step"] = "error"` — never raise
- `pytest.skip()` used in integration tests when infrastructure is unavailable (not `pytest.fail()`)

### Logging

**Framework:** Python `logging` module
- Every agent node module declares `logger = logging.getLogger(__name__)` at module level
- No log calls in service layer — logging is at the agent/node level

### Comments / Docstrings

**Module docstrings:** Every module file has a one-line `"""..."""` docstring describing its purpose.
**Function docstrings:** Used on public functions and complex helpers; single-line for simple ones.
**Inline comments:** Used for non-obvious logic (e.g., `# Detect if connecting to remote Supabase (needs SSL)`).

---

## TypeScript / Svelte (frontend)

### Naming Patterns

**Files:**
- SvelteKit routes use `+page.svelte`, `+layout.svelte`, `+page.server.ts` conventions
- Component files: `PascalCase.svelte` — `ProjectCard.svelte`, `ObjectEditor.svelte`
- Store files: `kebab-case.svelte.ts` — `objects.svelte.ts`, `workflow.svelte.ts`
- Service files: `kebab-case.ts` — `api.ts`, `generated-objects.ts`, `push-websocket.ts`
- Type files: `kebab-case.ts` — `workflow.ts`, `push.ts`, `document.ts`
- Test files: co-located, same name + `.test.ts` — `objects.svelte.test.ts`, `ProjectCard.svelte.test.ts`

**Functions / Variables:**
- `camelCase` for all variables and functions: `createWorkflowService()`, `mockObjectService()`, `makeMockObject()`
- `PascalCase` for classes: `ObjectsStore`, `ApiClient`, `ApiError`
- Exported constants use `SCREAMING_SNAKE_CASE`: `ENTITY_TYPE_ORDER`, `OBJECT_STATUSES`, `PUSHABLE_STATUSES`

**Types / Interfaces:**
- Interfaces use `PascalCase`: `WorkflowService`, `EntityGroup`, `GeneratedObjectService`
- Discriminated union type aliases for domain enums: `EntityType`, `ObjectStatus`, `WorkflowType`
- All domain types are defined and re-exported from `src/lib/types/index.ts`

### Code Style

**Formatting:**
- Prettier with `prettier-plugin-svelte` and `prettier-plugin-tailwindcss`
- Tab-based indentation (Prettier default for Svelte)
- Double quotes for strings (Prettier default)

**Linting:**
- ESLint with `typescript-eslint` + `eslint-plugin-svelte`
- `@typescript-eslint/no-explicit-any` is disabled in test files only
- `svelte/no-navigation-without-resolve`, `svelte/require-each-key`, `no-useless-assignment` are disabled for shadcn-svelte component compatibility

**Svelte 5 Runes (mandatory):**
- All reactive state uses `$state`: `objects = $state<GeneratedObject[]>([])`
- Derived values use `$derived` or `$derived.by()` for complex derivations
- Never use legacy `writable()` or `readable()` stores
- All `<script>` blocks must have `lang="ts"`

### Import Organization

**Path Aliases (always use, never relative `../../`):**
- `$lib` → `src/lib`
- `$components` → `src/lib/components`
- `$stores` → `src/lib/stores`
- `$services` → `src/lib/services`
- `$types` → `src/lib/types`

**Import style:**
- External packages first, then `$lib/*` aliases
- Types imported with `import type { ... }` when type-only

### Module Design

**Services (factory function pattern):**
```typescript
// Factory function — NOT a singleton, NOT a class
export function createWorkflowService(client: ApiClient): WorkflowService {
  return {
    list: (useCaseId) => client.get<Workflow[]>(`/api/use-cases/${useCaseId}/workflows`),
    // ...
  };
}
```
All service modules follow this pattern: `createGeneratedObjectService`, `createWorkflowService`, `createProjectService`.

**Stores (class-based Svelte 5 runes singleton):**
```typescript
class ObjectsStore {
  objects = $state<GeneratedObject[]>([]);
  loading = $state(false);
  filteredObjects = $derived.by(() => { ... });

  async loadObjects(service: GeneratedObjectService, useCaseId: string) { ... }
}
export const objectsStore = new ObjectsStore();
```
Stores are exported as module-level singletons. Test files import them dynamically to get a fresh module instance.

**Utility function:**
- `cn(...classes)` from `$lib/utils.ts` for all conditional Tailwind class merging — never raw string concatenation

### Error Handling

**Pattern:**
- Service methods throw `ApiError` (custom class in `src/lib/services/api.ts`) for non-OK HTTP responses
- Stores catch errors and set `store.error = e.message` — never propagate to components
- Store methods return result objects: `{ ok: true, created: obj }` or `{ ok: false, error: string }` for operations with meaningful failures

### Comments

**When to Comment:**
- Complex `$derived.by()` logic
- Non-obvious WebSocket protocol notes
- Disambiguating shadcn-svelte workarounds

---

## Shared (`shared/` directory)

- JSON files only — entity type lists, status enums, shared constants
- Consumed by both frontend (via import) and backend (via Python file reads)

---

*Convention analysis: 2026-03-22*
