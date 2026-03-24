<script lang="ts">
	import { invalidate } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { DiagramCard, CreateDiagramDialog, DeleteDiagramDialog } from '$lib/components/diagram';
	import { EmptyState } from '$lib/components/project';
	import { diagramStore } from '$lib/stores';
	import { createApiClient, createDiagramService } from '$lib/services';
	import { Plus, Network } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import type { DiagramCreate } from '$lib/types';

	let { data } = $props();

	let createOpen = $state(false);
	let deleteOpen = $state(false);
	let deletingDiagram = $state<{ id: string; name: string } | null>(null);

	$effect(() => {
		diagramStore.diagrams = data.diagrams;
	});

	async function handleCreate(formData: DiagramCreate) {
		const client = createApiClient(data.supabase);
		const service = createDiagramService(client);
		const diagram = await diagramStore.createDiagram(service, formData);
		if (diagram) {
			toast.success('Diagram created');
			createOpen = false;
			await invalidate('app:diagrams');
		} else {
			toast.error(diagramStore.error ?? 'Failed to create diagram');
		}
	}

	function openDelete(id: string) {
		const diagram = diagramStore.diagrams.find((d) => d.id === id);
		if (diagram) {
			deletingDiagram = {
				id: diagram.id,
				name: diagram.customer_name || diagram.title || 'Untitled',
			};
			deleteOpen = true;
		}
	}

	async function handleDelete() {
		if (!deletingDiagram) return;
		const client = createApiClient(data.supabase);
		const service = createDiagramService(client);
		const ok = await diagramStore.deleteDiagram(service, deletingDiagram.id);
		if (ok) {
			toast.success('Diagram deleted');
			deleteOpen = false;
			deletingDiagram = null;
			await invalidate('app:diagrams');
		} else {
			toast.error(diagramStore.error ?? 'Failed to delete diagram');
			deleteOpen = false;
		}
	}
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-semibold tracking-tight">Diagrams</h1>
			<p class="text-muted-foreground mt-1">Create integration architecture diagrams.</p>
		</div>
		<Button onclick={() => (createOpen = true)}>
			<Plus class="mr-2 size-4" />
			New Diagram
		</Button>
	</div>

	{#if diagramStore.sortedDiagrams.length === 0}
		<EmptyState
			icon={Network}
			title="No diagrams yet"
			description="Create your first integration architecture diagram."
			actionLabel="New Diagram"
			onaction={() => (createOpen = true)}
		/>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each diagramStore.sortedDiagrams as diagram (diagram.id)}
				<DiagramCard {diagram} ondelete={openDelete} />
			{/each}
		</div>
	{/if}
</div>

<CreateDiagramDialog bind:open={createOpen} projects={data.projects} oncreate={handleCreate} />

<DeleteDiagramDialog
	bind:open={deleteOpen}
	diagramName={deletingDiagram?.name ?? ''}
	onconfirm={handleDelete}
/>
