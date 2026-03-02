# Control Panel as Use Case Home — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the Control Panel the primary use case view, with workflows launching in a side drawer instead of a separate page.

**Architecture:** The `/workflow` route is removed entirely. The control panel page gains workflow capabilities: a toolbar dropdown to pick and start workflows, a Sheet (right-side drawer) containing the chat UI, and live object refetching when workflows produce new entities. The existing `workflowStore` singleton is reused as-is.

**Tech Stack:** SvelteKit, Svelte 5 runes, shadcn-svelte (Sheet, DropdownMenu, Select, Button), TypeScript

**Design doc:** `docs/plans/2026-03-02-control-panel-as-use-case-home-design.md`

---

### Task 1: Update Control Panel Data Loading

**Files:**
- Modify: `frontend/src/routes/(app)/projects/[projectId]/use-cases/[useCaseId]/control-panel/+page.ts`

**Step 1: Add workflow + model data to the load function**

The current load function fetches `useCase`, `project`, and `objects`. Add `workflows`, `models`, `interruptedWorkflow`, and `interruptedMessages` — matching exactly what the workflow `+page.ts` does today.

```typescript
import { error } from '@sveltejs/kit';
import {
	createApiClient,
	createUseCaseService,
	createProjectService,
	createGeneratedObjectService,
	createWorkflowService,
} from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent, params }) => {
	const { supabase, session } = await parent();
	const client = createApiClient(supabase, session?.access_token);
	const useCaseService = createUseCaseService(client);
	const projectService = createProjectService(client);
	const objectService = createGeneratedObjectService(client);
	const workflowService = createWorkflowService(client);

	// Use case is required
	let useCase;
	try {
		useCase = await useCaseService.get(params.useCaseId);
	} catch {
		error(404, 'Use case not found');
	}

	// Secondary data can fail gracefully
	const [project, objects, workflows, models] = await Promise.allSettled([
		projectService.get(params.projectId),
		objectService.listObjects(params.useCaseId),
		workflowService.list(params.useCaseId),
		workflowService.listModels(),
	]);

	// Find any interrupted workflow
	const workflowList = workflows.status === 'fulfilled' ? workflows.value : [];
	const interruptedWorkflow = workflowList.find((w) => w.status === 'interrupted');

	// Load messages for interrupted workflow
	let interruptedMessages: Awaited<ReturnType<typeof workflowService.listMessages>> = [];
	if (interruptedWorkflow) {
		try {
			interruptedMessages = await workflowService.listMessages(interruptedWorkflow.id);
		} catch {
			// Graceful failure
		}
	}

	return {
		useCase,
		project: project.status === 'fulfilled' ? project.value : null,
		objects: objects.status === 'fulfilled' ? objects.value : [],
		workflows: workflowList,
		models: models.status === 'fulfilled' ? models.value : [],
		interruptedWorkflow: interruptedWorkflow ?? null,
		interruptedMessages,
		session,
	};
};
```

**Step 2: Verify the page loads without errors**

Run the dev server and navigate to the control panel page. Confirm no TypeScript errors and that the existing control panel still renders.

**Step 3: Commit**

```bash
git add frontend/src/routes/(app)/projects/\[projectId\]/use-cases/\[useCaseId\]/control-panel/+page.ts
git commit -m "feat: add workflow + model data to control panel load function"
```

---

### Task 2: Create WorkflowLauncherDropdown Component

**Files:**
- Create: `frontend/src/lib/components/control-panel/WorkflowLauncherDropdown.svelte`

**Step 1: Build the dropdown component**

Uses shadcn-svelte `DropdownMenu` with nested `Select` for model picker. Includes prerequisite gating logic extracted from the existing `WorkflowLauncher.svelte` (lines 27-39). Uses `Play` icon from lucide-svelte.

```svelte
<script lang="ts">
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Play, Check } from 'lucide-svelte';
	import { cn, snakeToTitle } from '$lib/utils.js';
	import type { LlmModel, Workflow, WorkflowType } from '$lib/types/workflow.js';

	let {
		models,
		workflows = [],
		loading = false,
		onstart,
	}: {
		models: LlmModel[];
		workflows?: Workflow[];
		loading?: boolean;
		onstart?: (modelId: string, workflowType: WorkflowType) => void | Promise<void>;
	} = $props();

	let selectedModelId = $state('');
	let selectedWorkflowType = $state<WorkflowType>('product_meter_aggregation');
	let open = $state(false);

	const selectedModelLabel = $derived(
		models.find((m) => m.id === selectedModelId)?.display_name || 'Select model...',
	);

	const hasCompletedWf1 = $derived(
		workflows.some(
			(w) => w.workflow_type === 'product_meter_aggregation' && w.status === 'completed',
		),
	);
	const hasCompletedWf2 = $derived(
		workflows.some((w) => w.workflow_type === 'plan_pricing' && w.status === 'completed'),
	);
	const hasCompletedWf3 = $derived(
		workflows.some((w) => w.workflow_type === 'account_setup' && w.status === 'completed'),
	);

	interface WfOption {
		type: WorkflowType;
		label: string;
		enabled: boolean;
		hint: string;
	}

	const workflowOptions = $derived<WfOption[]>([
		{
			type: 'product_meter_aggregation',
			label: 'Products, Meters & Aggregations',
			enabled: true,
			hint: 'Core billing entities',
		},
		{
			type: 'plan_pricing',
			label: 'Plans & Pricing',
			enabled: hasCompletedWf1,
			hint: hasCompletedWf1 ? 'Plan templates, plans, pricing' : 'Complete WF1 first',
		},
		{
			type: 'account_setup',
			label: 'Accounts & Account Plans',
			enabled: hasCompletedWf2,
			hint: hasCompletedWf2 ? 'Customer accounts' : 'Complete WF2 first',
		},
		{
			type: 'usage_submission',
			label: 'Usage & Measurements',
			enabled: hasCompletedWf3,
			hint: hasCompletedWf3 ? 'Sample usage data' : 'Complete WF3 first',
		},
	]);

	async function handleStart() {
		if (!selectedModelId || loading) return;
		open = false;
		await onstart?.(selectedModelId, selectedWorkflowType);
	}
</script>

<DropdownMenu.Root bind:open>
	<DropdownMenu.Trigger>
		{#snippet child({ props })}
			<Button size="sm" {...props}>
				<Play class="mr-1 size-4" />
				Run Workflow
			</Button>
		{/snippet}
	</DropdownMenu.Trigger>
	<DropdownMenu.Content class="w-72 p-3" align="end">
		<div class="space-y-3">
			<div class="space-y-1">
				<p class="text-xs font-medium text-muted-foreground">Workflow Type</p>
				{#each workflowOptions as opt (opt.type)}
					<button
						class={cn(
							'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
							!opt.enabled && 'cursor-not-allowed opacity-50',
							opt.enabled && selectedWorkflowType === opt.type && 'bg-accent',
							opt.enabled && selectedWorkflowType !== opt.type && 'hover:bg-accent/50',
						)}
						disabled={!opt.enabled}
						onclick={() => {
							if (opt.enabled) selectedWorkflowType = opt.type;
						}}
					>
						<Check
							class={cn(
								'size-3.5 shrink-0',
								selectedWorkflowType === opt.type ? 'opacity-100' : 'opacity-0',
							)}
						/>
						<div>
							<div class="font-medium">{opt.label}</div>
							<div class="text-xs text-muted-foreground">{opt.hint}</div>
						</div>
					</button>
				{/each}
			</div>

			<div class="space-y-1">
				<p class="text-xs font-medium text-muted-foreground">AI Model</p>
				<Select.Root type="single" bind:value={selectedModelId}>
					<Select.Trigger class="w-full">{selectedModelLabel}</Select.Trigger>
					<Select.Content>
						{#each models as model (model.id)}
							<Select.Item value={model.id}>{model.display_name}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>

			<Button class="w-full" size="sm" onclick={handleStart} disabled={!selectedModelId || loading}>
				{loading ? 'Starting...' : 'Start'}
			</Button>
		</div>
	</DropdownMenu.Content>
</DropdownMenu.Root>
```

**Step 2: Export from control-panel barrel**

Add to `frontend/src/lib/components/control-panel/index.ts`:

```typescript
export { default as WorkflowLauncherDropdown } from './WorkflowLauncherDropdown.svelte';
```

**Step 3: Commit**

```bash
git add frontend/src/lib/components/control-panel/WorkflowLauncherDropdown.svelte frontend/src/lib/components/control-panel/index.ts
git commit -m "feat: add WorkflowLauncherDropdown component for control panel toolbar"
```

---

### Task 3: Create WorkflowDrawer Component

**Files:**
- Create: `frontend/src/lib/components/control-panel/WorkflowDrawer.svelte`

**Step 1: Build the drawer component**

Uses shadcn-svelte `Sheet` (side="right") to wrap `WorkflowHeader` + `ChatContainer`. The Sheet component's default max-width (`sm:max-w-sm`) is too narrow — override to `sm:max-w-lg` (512px) via the `class` prop on `Sheet.Content`.

```svelte
<script lang="ts">
	import * as Sheet from '$lib/components/ui/sheet';
	import { ChatContainer, WorkflowHeader } from '$lib/components/chat';
	import type {
		ChatMessage,
		EntityDecision,
		ClarificationAnswer,
		WsConnectionState,
		WorkflowStatus,
	} from '$lib/types';

	let {
		open = $bindable(false),
		messages,
		thinking,
		currentStep,
		connectionState,
		status,
		modelName,
		pendingDecisions,
		ondecision,
		onclarify,
	}: {
		open: boolean;
		messages: ChatMessage[];
		thinking: boolean;
		currentStep: string;
		connectionState: WsConnectionState;
		status: WorkflowStatus | null;
		modelName: string;
		pendingDecisions: EntityDecision[];
		ondecision: (decision: EntityDecision) => void;
		onclarify: (answers: ClarificationAnswer[]) => void;
	} = $props();
</script>

<Sheet.Root bind:open>
	<Sheet.Content side="right" class="flex w-full flex-col p-0 sm:max-w-lg">
		<Sheet.Header class="sr-only">
			<Sheet.Title>Workflow</Sheet.Title>
			<Sheet.Description>AI workflow chat panel</Sheet.Description>
		</Sheet.Header>
		<WorkflowHeader
			{currentStep}
			{connectionState}
			{status}
			{modelName}
		/>
		<div class="flex-1 overflow-hidden">
			<ChatContainer
				{messages}
				{thinking}
				{currentStep}
				{pendingDecisions}
				{ondecision}
				{onclarify}
			/>
		</div>
	</Sheet.Content>
</Sheet.Root>
```

**Step 2: Export from control-panel barrel**

Add to `frontend/src/lib/components/control-panel/index.ts`:

```typescript
export { default as WorkflowDrawer } from './WorkflowDrawer.svelte';
```

**Step 3: Commit**

```bash
git add frontend/src/lib/components/control-panel/WorkflowDrawer.svelte frontend/src/lib/components/control-panel/index.ts
git commit -m "feat: add WorkflowDrawer component using Sheet side panel"
```

---

### Task 4: Integrate Workflow into Control Panel Page

**Files:**
- Modify: `frontend/src/routes/(app)/projects/[projectId]/use-cases/[useCaseId]/control-panel/+page.svelte`

**Step 1: Add workflow imports, store init, and handlers**

Add these imports and logic to the existing `<script>` block. This merges the workflow page's logic into the control panel page. Key additions:

1. Import `workflowStore` and new components
2. Import `createWorkflowService` service
3. Add workflow initialization in `$effect` (models, workflows, interrupted restore)
4. Add `handleStart`, `handleDecision`, `handleClarification` handlers
5. Add `drawerOpen` state
6. Add derived `modelName`
7. Add `$effect` to open drawer when workflow starts
8. Add `$effect` to auto-close drawer + refetch objects on workflow completion
9. Add `$effect` to refetch objects when status messages indicate entity approval
10. Add `onDestroy` to clear workflowStore

New imports to add at top of `<script>`:

```typescript
import { workflowStore } from '$lib/stores';
import { createWorkflowService } from '$lib/services';
import { WorkflowLauncherDropdown, WorkflowDrawer } from '$lib/components/control-panel';
import type { EntityDecision, ClarificationAnswer, WorkflowType } from '$lib/types/workflow.js';
```

Add these state and derived values:

```typescript
let drawerOpen = $state(false);
let workflowInitialized = false;

const workflowService = $derived(createWorkflowService(createApiClient(data.supabase)));

const modelName = $derived(
	workflowStore.models.find((m) => m.id === workflowStore.workflow?.model_id)?.display_name ?? '',
);
```

Add workflow initialization inside the existing `$effect` or as a new `$effect`:

```typescript
// Initialize workflow store with page data
$effect(() => {
	workflowStore.models = data.models;
	workflowStore.workflows = data.workflows;

	// Restore interrupted workflow once
	if (!workflowInitialized && data.interruptedWorkflow && data.session?.access_token) {
		workflowInitialized = true;
		workflowStore.restoreFromInterrupt(
			data.interruptedWorkflow,
			data.session.access_token,
			data.interruptedMessages,
		);
		drawerOpen = true;
	}
});
```

Add auto-close + refetch effect:

```typescript
// Auto-close drawer and refetch objects when workflow completes
$effect(() => {
	if (workflowStore.isCompleted && drawerOpen) {
		const timer = setTimeout(() => {
			drawerOpen = false;
			// Refetch objects to show newly generated entities
			service.listObjects(page.params.useCaseId!).then((objs) => {
				objectsStore.objects = objs;
			});
			// Refresh workflows list for prerequisite gating
			workflowStore.loadWorkflows(workflowService, data.useCase.id);
		}, 3000);
		return () => clearTimeout(timer);
	}
});
```

Add refetch on status messages (when entities get approved, the WS sends a new status step — refetch at that point):

```typescript
// Refetch objects when workflow moves to a new step (entities were just approved/saved)
let prevMessageCount = $state(0);
$effect(() => {
	const count = workflowStore.messages.length;
	if (count > prevMessageCount && prevMessageCount > 0) {
		const lastMsg = workflowStore.messages[count - 1];
		if (lastMsg?.type === 'status') {
			// A new step started — previous step's entities were saved to DB
			service.listObjects(page.params.useCaseId!).then((objs) => {
				objectsStore.objects = objs;
			});
		}
	}
	prevMessageCount = count;
});
```

Add handlers:

```typescript
async function handleStartWorkflow(modelId: string, workflowType: WorkflowType) {
	if (!data.session?.access_token) {
		toast.error('Not authenticated');
		return;
	}
	const wf = await workflowStore.startWorkflow(
		workflowService,
		data.useCase.id,
		modelId,
		data.session.access_token,
		workflowType,
	);
	if (wf) {
		drawerOpen = true;
	} else {
		toast.error(workflowStore.error ?? 'Failed to start workflow');
	}
}

function handleDecision(decision: EntityDecision) {
	workflowStore.submitDecision(decision);
}

function handleClarification(answers: ClarificationAnswer[]) {
	workflowStore.submitClarificationAnswers(answers);
}
```

Update the existing `onDestroy` to also clear workflow store:

```typescript
onDestroy(() => {
	objectsStore.clear();
	workflowStore.clear();
});
```

**Step 2: Update the template**

Replace the top bar and add the drawer. The "Back to Workflow" button becomes "Back" pointing to the project page. Add the `WorkflowLauncherDropdown` next to the "New Object" button. Add `WorkflowDrawer` at the bottom of the template.

Replace the top bar section (lines 130-147 in current file):

```svelte
<!-- Top bar -->
<div class="flex items-center gap-3 border-b px-4 py-3">
	<Button variant="ghost" size="sm" href="/projects/{page.params.projectId}">
		<ArrowLeft class="mr-1 size-4" />
		Back
	</Button>
	<div class="flex-1">
		<h1 class="text-sm font-semibold">Control Panel</h1>
		<p class="text-muted-foreground text-xs">{data.useCase.title}</p>
	</div>
	<WorkflowLauncherDropdown
		models={workflowStore.models}
		workflows={workflowStore.workflows}
		loading={workflowStore.loading}
		onstart={handleStartWorkflow}
	/>
	<Button size="sm" onclick={() => (showCreateDialog = true)}>
		<Plus class="mr-1 size-4" />
		New Object
	</Button>
</div>
```

Add the drawer right before the closing `</div>` of the root element (before `CreateObjectDialog` and `PushConfirmDialog`):

```svelte
<WorkflowDrawer
	bind:open={drawerOpen}
	messages={workflowStore.messages}
	thinking={workflowStore.thinking}
	currentStep={workflowStore.currentStep}
	connectionState={workflowStore.connectionState}
	status={workflowStore.workflow?.status ?? null}
	{modelName}
	pendingDecisions={workflowStore.pendingDecisions}
	ondecision={handleDecision}
	onclarify={handleClarification}
/>
```

**Step 3: Verify it works**

Run dev server, navigate to a use case's control panel. Verify:
- "Run Workflow" button appears in toolbar
- Clicking opens dropdown with workflow types and model picker
- Starting a workflow opens the sheet drawer from the right
- Chat messages appear in the drawer
- After completion, drawer auto-closes and objects refresh in the tree

**Step 4: Commit**

```bash
git add frontend/src/routes/(app)/projects/\[projectId\]/use-cases/\[useCaseId\]/control-panel/+page.svelte
git commit -m "feat: integrate workflow side panel into control panel page"
```

---

### Task 5: Update UseCaseCard Link Target

**Files:**
- Modify: `frontend/src/lib/components/project/UseCaseCard.svelte`

**Step 1: Change the link from `/workflow` to `/control-panel`**

In `UseCaseCard.svelte`, update line 20-22:

Change:
```typescript
const workflowHref = $derived(
	projectId ? `/projects/${projectId}/use-cases/${useCase.id}/workflow` : undefined,
);
```

To:
```typescript
const href = $derived(
	projectId ? `/projects/${projectId}/use-cases/${useCase.id}/control-panel` : undefined,
);
```

Also update the template references from `workflowHref` to `href` (lines 25-27 and 50-55):

Change the `<a>` tag:
```svelte
<a
	href={href}
	class={cn('block transition-shadow hover:shadow-md', href && 'cursor-pointer')}
>
```

Change the bottom text from "Open Workflow" to "Open":
```svelte
{#if href}
	<span class="flex items-center gap-1 text-xs">
		Open
		<ArrowRight class="size-3" />
	</span>
{/if}
```

**Step 2: Commit**

```bash
git add frontend/src/lib/components/project/UseCaseCard.svelte
git commit -m "feat: link UseCaseCard to control panel instead of workflow"
```

---

### Task 6: Delete the Workflow Route

**Files:**
- Delete: `frontend/src/routes/(app)/projects/[projectId]/use-cases/[useCaseId]/workflow/+page.svelte`
- Delete: `frontend/src/routes/(app)/projects/[projectId]/use-cases/[useCaseId]/workflow/+page.ts`

**Step 1: Remove the workflow route files**

```bash
rm frontend/src/routes/\(app\)/projects/\[projectId\]/use-cases/\[useCaseId\]/workflow/+page.svelte
rm frontend/src/routes/\(app\)/projects/\[projectId\]/use-cases/\[useCaseId\]/workflow/+page.ts
rmdir frontend/src/routes/\(app\)/projects/\[projectId\]/use-cases/\[useCaseId\]/workflow/
```

**Step 2: Check for any remaining references to the workflow route**

Search the codebase for any links or references to the `/workflow` path that need updating:

```bash
grep -r "workflow" frontend/src/ --include="*.svelte" --include="*.ts" -l
```

Specifically look for URL patterns like `/workflow` in `href` attributes or `goto()` calls. Known places to check:
- Any breadcrumb components
- Any navigation helpers

**Step 3: Verify no broken links**

Run the dev server. Navigate through: Dashboard → Project → Use Case Card → should land on Control Panel (not 404).

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: remove standalone workflow route, control panel is now the primary use case view"
```

---

### Task 7: Cleanup and Polish

**Files:**
- Modify: `frontend/src/lib/components/chat/index.ts` (remove WorkflowLauncher export if no longer used)
- Potentially delete: `frontend/src/lib/components/chat/WorkflowLauncher.svelte` (the full-page launcher is replaced by the dropdown)

**Step 1: Check if WorkflowLauncher is still imported anywhere**

```bash
grep -r "WorkflowLauncher" frontend/src/ --include="*.svelte" --include="*.ts"
```

If no remaining imports (the workflow page that used it is deleted), remove it:

- Delete `frontend/src/lib/components/chat/WorkflowLauncher.svelte`
- Remove `export { default as WorkflowLauncher } from './WorkflowLauncher.svelte';` from `frontend/src/lib/components/chat/index.ts`

**Step 2: Run lint and type check**

```bash
cd frontend && npm run check && npm run lint
```

Fix any TypeScript or lint errors.

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove unused WorkflowLauncher component, fix lint"
```

---

### Task 8: Update Documentation

**Files:**
- Modify: `AGENTS.md` — update Frontend Chat Interface section, control panel docs, route descriptions
- Modify: `docs/ROADMAP.md` — if applicable

**Step 1: Update AGENTS.md**

Key changes:
- In "Frontend Chat Interface" section: note that WorkflowLauncher is replaced by WorkflowLauncherDropdown in the control panel
- Update "Workflow route" entry from `/workflow/` to note it's now a Sheet drawer in the control panel
- In "Frontend Control Panel" section: add WorkflowDrawer, WorkflowLauncherDropdown, note that control panel is the primary use case view
- Update "Component tree" to reflect the new structure

**Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: update AGENTS.md for control panel as primary use case view"
```
