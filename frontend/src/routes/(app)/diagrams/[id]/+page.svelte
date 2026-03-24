<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { DiagramRenderer, AddCustomSystemDialog } from '$lib/components/diagram';
	import { diagramStore } from '$lib/stores';
	import { createApiClient, createDiagramService } from '$lib/services';
	import { Plus, ArrowLeft } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import type { DiagramSystem } from '$lib/types';

	let { data } = $props();

	let addSystemOpen = $state(false);

	// Build service in component (not from route data) -- addresses review HIGH concern
	const service = $derived.by(() => {
		const client = createApiClient(data.supabase, data.session?.access_token);
		return createDiagramService(client);
	});

	$effect(() => {
		diagramStore.currentDiagram = data.diagram;
		diagramStore.componentLibrary = data.components;
		return () => diagramStore.clearEditor();
	});

	async function handleAddSystem(system: DiagramSystem) {
		diagramStore.addSystem(system);
		addSystemOpen = false;
		toast.success(`Added ${system.name}`);
		// Persist through store's updateContent (not bypassing the store)
		if (diagramStore.currentDiagram) {
			await diagramStore.updateContent(service, diagramStore.currentDiagram.content);
			if (diagramStore.error) {
				toast.error('Failed to save diagram');
			}
		}
	}
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-3">
			<Button variant="ghost" size="icon" onclick={() => goto('/diagrams')}>
				<ArrowLeft class="size-4" />
			</Button>
			<div>
				<h1 class="text-xl font-semibold">
					{diagramStore.currentDiagram?.customer_name ?? 'Diagram'}
				</h1>
				{#if diagramStore.currentDiagram?.title}
					<p class="text-muted-foreground text-sm">{diagramStore.currentDiagram.title}</p>
				{/if}
			</div>
		</div>
		<Button onclick={() => (addSystemOpen = true)} aria-label="Add Custom System">
			<Plus class="mr-2 size-4" />
			Add Custom System
		</Button>
	</div>

	{#if diagramStore.currentDiagram}
		<div class="overflow-hidden rounded-lg border shadow-sm">
			<DiagramRenderer
				content={diagramStore.currentDiagram.content}
				componentLibrary={diagramStore.componentLibrary}
			/>
		</div>
	{:else if diagramStore.error}
		<div class="py-12 text-center">
			<h2 class="text-lg font-semibold">Failed to load diagram</h2>
			<p class="text-muted-foreground mt-2">
				This diagram could not be loaded. Go back and try again.
			</p>
		</div>
	{/if}
</div>

<AddCustomSystemDialog
	bind:open={addSystemOpen}
	onsubmit={handleAddSystem}
	supabase={data.supabase}
	accessToken={data.session?.access_token}
/>
