<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { page } from '$app/state';
	import {
		ObjectTree,
		ObjectEditor,
		BulkActions,
		CreateObjectDialog,
		PushProgressPanel,
		PushConfirmDialog,
		UseCaseMetadataPanel,
		WorkflowLauncherDropdown,
		WorkflowDrawer,
	} from '$lib/components/control-panel';
	import { objectsStore, workflowStore } from '$lib/stores';
	import {
		createApiClient,
		createGeneratedObjectService,
		createUseCaseService,
		createWorkflowService,
	} from '$lib/services';
	import { toast } from 'svelte-sonner';
	import { ArrowLeft, Plus } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { snakeToTitle } from '$lib/utils.js';
	import type {
		UseCase,
		UseCaseUpdate,
		GeneratedObjectUpdate,
		ObjectStatus,
		CreateObjectPayload,
	} from '$lib/types';
	import type { EntityDecision, ClarificationAnswer, WorkflowType } from '$lib/types/workflow.js';

	let { data } = $props();
	let initialized = false;
	let useCase = $state<UseCase>(data.useCase);
	let useCaseSaving = $state(false);
	let showCreateDialog = $state(false);
	let templates = $state<Record<string, Record<string, unknown>>>({});
	let showPushConfirm = $state(false);
	let pushTargetIds = $state<string[]>([]);
	let drawerOpen = $state(false);
	let workflowInitialized = false;

	const apiClient = $derived(createApiClient(data.supabase));
	const service = $derived(createGeneratedObjectService(apiClient));
	const useCaseService = $derived(createUseCaseService(apiClient));
	const workflowService = $derived(createWorkflowService(apiClient));
	const objectCount = $derived(objectsStore.objects.length);

	const modelName = $derived(
		workflowStore.models.find((m) => m.id === workflowStore.workflow?.model_id)?.display_name ?? '',
	);

	// Initialize store with loaded data once; skip re-runs from session refresh
	$effect(() => {
		if (!initialized) {
			initialized = true;
			objectsStore.clear();
		}
		objectsStore.objects = data.objects;
	});

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

	// Auto-close drawer when workflow completes (not on failure)
	$effect(() => {
		if (workflowStore.isCompleted && drawerOpen) {
			const timer = setTimeout(() => {
				drawerOpen = false;
			}, 5000);
			return () => clearTimeout(timer);
		}
	});

	// Refresh objects and workflows when drawer closes
	let prevDrawerOpen = false;
	$effect(() => {
		if (prevDrawerOpen && !drawerOpen) {
			service.listObjects(page.params.useCaseId!).then((objs) => {
				objectsStore.objects = objs;
			});
			workflowStore.loadWorkflows(workflowService, data.useCase.id);
		}
		prevDrawerOpen = drawerOpen;
	});

	// On failure, refresh workflows immediately so prerequisite gating reflects the failed state
	$effect(() => {
		if (workflowStore.isFailed) {
			workflowStore.loadWorkflows(workflowService, data.useCase.id);
		}
	});

	// Refetch objects when workflow moves to a new step (entities were just approved/saved)
	let prevMessageCount = 0;
	$effect(() => {
		const count = workflowStore.messages.length;
		if (count > prevMessageCount && prevMessageCount > 0) {
			const lastMsg = workflowStore.messages[count - 1];
			if (lastMsg?.type === 'status') {
				service.listObjects(page.params.useCaseId!).then((objs) => {
					objectsStore.objects = objs;
				});
			}
		}
		prevMessageCount = count;
	});

	// Derive which object IDs are currently being pushed (for tree spinner display)
	const pushingObjectIds = $derived.by(() => {
		const ids = new Set<string>(); // eslint-disable-line svelte/prefer-svelte-reactivity -- read-only derived, not used as reactive state
		if (objectsStore.pushSession?.active) {
			for (const item of objectsStore.pushSession.items) {
				if (item.status === 'pushing') {
					ids.add(item.entityId);
				}
			}
		}
		return ids;
	});

	// Derive the objects to show in the push confirm dialog
	const pushTargetObjects = $derived.by(() => {
		const idSet = new Set(pushTargetIds);
		return objectsStore.objects.filter((o) => idSet.has(o.id));
	});

	async function handleUpdate(id: string, updateData: GeneratedObjectUpdate) {
		const result = await objectsStore.updateObject(service, id, updateData);
		if (result.ok) {
			toast.success('Object updated');
		} else {
			toast.error(result.error);
		}
	}

	async function handleBulkAction(status: ObjectStatus) {
		const ids = [...objectsStore.selectedIds];
		if (ids.length === 0) return;
		const result = await objectsStore.bulkUpdateStatus(service, ids, status);
		if (result.ok) {
			const label = snakeToTitle(status);
			toast.success(`${label} ${ids.length} object${ids.length > 1 ? 's' : ''}`);
		} else {
			toast.error(result.error);
		}
	}

	async function handlePushSingle(objectId: string) {
		const result = await objectsStore.pushSingleObject(service, objectId);
		if (result.ok) {
			toast.success('Object pushed to m3ter');
		} else {
			toast.error(result.error);
		}
	}

	function handleBulkPushRequest() {
		const ids = [...objectsStore.pushableSelectedIds];
		if (ids.length === 0) return;
		pushTargetIds = ids;
		showPushConfirm = true;
	}

	async function handleBulkPushConfirm() {
		showPushConfirm = false;
		const token = data.session?.access_token;
		if (!token) {
			toast.error('Authentication required for push');
			return;
		}
		const useCaseId = page.params.useCaseId!;
		objectsStore.startBulkPush(useCaseId, pushTargetIds, token);
	}

	onMount(() => {
		service
			.getTemplates()
			.then((t) => (templates = t))
			.catch(() => toast.error('Failed to load object templates'));
	});

	async function handleCreate(payload: CreateObjectPayload): Promise<boolean> {
		const useCaseId = page.params.useCaseId!;
		const result = await objectsStore.createObject(service, useCaseId, payload);
		if (result.ok) {
			toast.success('Object created');
			return true;
		}
		toast.error(result.error);
		return false;
	}

	async function handleUseCaseUpdate(updateData: UseCaseUpdate): Promise<UseCase | null> {
		useCaseSaving = true;
		try {
			const updated = await useCaseService.update(useCase.id, updateData);
			useCase = updated;
			toast.success('Use case updated');
			return updated;
		} catch {
			toast.error('Failed to update use case');
			return null;
		} finally {
			useCaseSaving = false;
		}
	}

	async function handleUseCaseReset(): Promise<void> {
		try {
			await useCaseService.reset(useCase.id);
			workflowStore.clear();
			await objectsStore.loadObjects(service, page.params.useCaseId!);
			toast.success('Objects reset');
		} catch {
			toast.error('Failed to reset objects');
		}
	}

	async function handleStartWorkflow(modelId: string, workflowType: WorkflowType) {
		// Guard: if a workflow is already active, reopen the drawer instead of orphaning it
		if (workflowStore.isRunning || workflowStore.isInterrupted) {
			drawerOpen = true;
			return;
		}
		// Prevent the restore-from-interrupt effect from disrupting this workflow
		// if a data refresh occurs (e.g., auth token refresh triggers load re-run)
		workflowInitialized = true;
		if (!data.session?.access_token) {
			toast.error('Not authenticated');
			return;
		}
		drawerOpen = true;
		const wf = await workflowStore.startWorkflow(
			workflowService,
			data.useCase.id,
			modelId,
			data.session.access_token,
			workflowType,
		);
		if (!wf) {
			drawerOpen = false;
			toast.error(workflowStore.error ?? 'Failed to start workflow');
		}
	}

	function handleDecision(decision: EntityDecision) {
		workflowStore.submitDecision(decision);
	}

	function handleApproveAll() {
		workflowStore.approveAll();
	}

	function handleClarification(answers: ClarificationAnswer[]) {
		workflowStore.submitClarificationAnswers(answers);
	}

	onDestroy(() => {
		objectsStore.clear();
		workflowStore.clear();
	});
</script>

<div class="flex h-full flex-col">
	<!-- Top bar -->
	<div class="flex items-center gap-3 border-b px-4 py-3">
		<Button variant="ghost" size="sm" href="/projects/{page.params.projectId}">
			<ArrowLeft class="mr-1 size-4" />
			Back
		</Button>
		<div class="flex-1">
			<h1 class="text-sm font-semibold">Control Panel</h1>
			<p class="text-muted-foreground text-xs">{useCase.title}</p>
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

	<!-- Bulk actions / filters -->
	<BulkActions
		filterEntityType={objectsStore.filterEntityType}
		filterStatus={objectsStore.filterStatus}
		searchQuery={objectsStore.searchQuery}
		selectedCount={objectsStore.selectedIds.size}
		totalCount={objectsStore.filteredObjects.length}
		pushableCount={objectsStore.pushableSelectedIds.size}
		pushing={objectsStore.pushing}
		onfilterEntityType={(v) => (objectsStore.filterEntityType = v)}
		onfilterStatus={(v) => (objectsStore.filterStatus = v)}
		onsearch={(v) => (objectsStore.searchQuery = v)}
		onapprove={() => handleBulkAction('approved')}
		onreject={() => handleBulkAction('rejected')}
		onpush={handleBulkPushRequest}
	/>

	<!-- Push progress panel -->
	{#if objectsStore.pushSession}
		<PushProgressPanel
			session={objectsStore.pushSession}
			ondismiss={() => objectsStore.dismissPushSession()}
		/>
	{/if}

	<!-- Main content: tree + editor -->
	<div class="flex flex-1 overflow-hidden">
		<!-- Object tree (left panel) -->
		<div class="w-80 shrink-0 overflow-y-auto border-r p-2">
			<UseCaseMetadataPanel
				{useCase}
				{objectCount}
				saving={useCaseSaving}
				workflowActive={workflowStore.isRunning || workflowStore.isInterrupted}
				onupdate={handleUseCaseUpdate}
				onreset={handleUseCaseReset}
			/>
			{#if objectsStore.loading}
				<div class="text-muted-foreground flex items-center justify-center p-8 text-sm">
					Loading objects...
				</div>
			{:else}
				<ObjectTree
					tree={objectsStore.tree}
					selectedObjectId={objectsStore.selectedObjectId}
					selectedIds={objectsStore.selectedIds}
					pushingIds={pushingObjectIds}
					onselect={(id) => objectsStore.selectObject(id)}
					ontoggle={(id) => objectsStore.toggleSelection(id)}
				/>
			{/if}
		</div>

		<!-- Object editor (right panel) -->
		<div class="flex-1 overflow-hidden">
			<ObjectEditor
				object={objectsStore.selectedObject}
				saving={objectsStore.saving}
				pushing={objectsStore.pushing}
				onupdate={handleUpdate}
				onpush={handlePushSingle}
			/>
		</div>
	</div>

	{#if objectsStore.error}
		<div class="bg-destructive/10 text-destructive border-t px-4 py-2 text-sm">
			{objectsStore.error}
		</div>
	{/if}

	<WorkflowDrawer
		bind:open={drawerOpen}
		loading={workflowStore.loading}
		messages={workflowStore.messages}
		thinking={workflowStore.thinking}
		currentStep={workflowStore.currentStep}
		connectionState={workflowStore.connectionState}
		status={workflowStore.workflow?.status ?? null}
		{modelName}
		pendingDecisions={workflowStore.pendingDecisions}
		hasPendingEntities={workflowStore.pendingEntities !== null}
		ondecision={handleDecision}
		onclarify={handleClarification}
		onapproveall={handleApproveAll}
	/>

	<CreateObjectDialog bind:open={showCreateDialog} {templates} oncreate={handleCreate} />

	<PushConfirmDialog
		bind:open={showPushConfirm}
		objects={pushTargetObjects}
		pushing={objectsStore.pushing}
		onconfirm={handleBulkPushConfirm}
		oncancel={() => (showPushConfirm = false)}
	/>
</div>
