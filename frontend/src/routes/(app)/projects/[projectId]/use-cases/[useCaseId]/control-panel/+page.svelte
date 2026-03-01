<script lang="ts">
	import { onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { ObjectTree, ObjectEditor, BulkActions } from '$lib/components/control-panel';
	import { objectsStore } from '$lib/stores';
	import { createApiClient, createGeneratedObjectService } from '$lib/services';
	import { toast } from 'svelte-sonner';
	import { ArrowLeft } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import type { GeneratedObjectUpdate, ObjectStatus } from '$lib/types';

	let { data } = $props();

	const service = $derived(createGeneratedObjectService(createApiClient(data.supabase)));

	// Clear and reinitialize store whenever loaded data changes (handles use-case navigation)
	$effect(() => {
		objectsStore.clear();
		objectsStore.objects = data.objects;
	});

	async function handleUpdate(id: string, updateData: GeneratedObjectUpdate) {
		const result = await objectsStore.updateObject(service, id, updateData);
		if (result) {
			toast.success('Object updated');
		} else {
			toast.error(objectsStore.error ?? 'Failed to update object');
		}
	}

	async function handleBulkAction(status: ObjectStatus) {
		const ids = [...objectsStore.selectedIds];
		if (ids.length === 0) return;
		await objectsStore.bulkUpdateStatus(service, ids, status);
		if (objectsStore.error) {
			toast.error(objectsStore.error);
		} else {
			const label = status.charAt(0).toUpperCase() + status.slice(1);
			toast.success(`${label} ${ids.length} object${ids.length > 1 ? 's' : ''}`);
		}
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
			href="/projects/{$page.params.projectId}/use-cases/{$page.params.useCaseId}/workflow"
		>
			<ArrowLeft class="mr-1 size-4" />
			Back to Workflow
		</Button>
		<div class="flex-1">
			<h1 class="text-sm font-semibold">Control Panel</h1>
			<p class="text-muted-foreground text-xs">{data.useCase.title}</p>
		</div>
	</div>

	<!-- Bulk actions / filters -->
	<BulkActions
		filterEntityType={objectsStore.filterEntityType}
		filterStatus={objectsStore.filterStatus}
		searchQuery={objectsStore.searchQuery}
		selectedCount={objectsStore.selectedIds.size}
		totalCount={objectsStore.filteredObjects.length}
		onfilterEntityType={(v) => (objectsStore.filterEntityType = v)}
		onfilterStatus={(v) => (objectsStore.filterStatus = v)}
		onsearch={(v) => (objectsStore.searchQuery = v)}
		onapprove={() => handleBulkAction('approved')}
		onreject={() => handleBulkAction('rejected')}
	/>

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
				onupdate={handleUpdate}
			/>
		</div>
	</div>

	{#if objectsStore.error}
		<div class="bg-destructive/10 text-destructive border-t px-4 py-2 text-sm">
			{objectsStore.error}
		</div>
	{/if}
</div>
