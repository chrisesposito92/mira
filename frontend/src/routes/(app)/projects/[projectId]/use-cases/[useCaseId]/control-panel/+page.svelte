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
	} from '$lib/components/control-panel';
	import { objectsStore } from '$lib/stores';
	import { createApiClient, createGeneratedObjectService } from '$lib/services';
	import { toast } from 'svelte-sonner';
	import { ArrowLeft, Plus } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { snakeToTitle } from '$lib/utils.js';
	import type { GeneratedObjectUpdate, ObjectStatus, CreateObjectPayload } from '$lib/types';

	let { data } = $props();
	let initialized = false;
	let showCreateDialog = $state(false);
	let templates = $state<Record<string, Record<string, unknown>>>({});
	let showPushConfirm = $state(false);
	let pushTargetIds = $state<string[]>([]);

	const service = $derived(createGeneratedObjectService(createApiClient(data.supabase)));

	// Initialize store with loaded data once; skip re-runs from session refresh
	$effect(() => {
		if (!initialized) {
			initialized = true;
			objectsStore.clear();
		}
		objectsStore.objects = data.objects;
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

	onDestroy(() => {
		objectsStore.clear();
	});
</script>

<div class="flex h-full flex-col">
	<!-- Top bar -->
	<div class="flex items-center gap-3 border-b px-4 py-3">
		<Button
			variant="ghost"
			size="sm"
			href="/projects/{page.params.projectId}/use-cases/{page.params.useCaseId}/workflow"
		>
			<ArrowLeft class="mr-1 size-4" />
			Back to Workflow
		</Button>
		<div class="flex-1">
			<h1 class="text-sm font-semibold">Control Panel</h1>
			<p class="text-muted-foreground text-xs">{data.useCase.title}</p>
		</div>
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

	<CreateObjectDialog bind:open={showCreateDialog} {templates} oncreate={handleCreate} />

	<PushConfirmDialog
		bind:open={showPushConfirm}
		objects={pushTargetObjects}
		pushing={objectsStore.pushing}
		onconfirm={handleBulkPushConfirm}
		oncancel={() => (showPushConfirm = false)}
	/>
</div>
