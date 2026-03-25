<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { DiagramRenderer, AddCustomSystemDialog } from '$lib/components/diagram';
	import BuilderSidebar from './builder/BuilderSidebar.svelte';
	import SaveStatusIndicator from './builder/SaveStatusIndicator.svelte';
	import { diagramStore } from '$lib/stores';
	import { createApiClient, createDiagramService } from '$lib/services';
	import { ArrowLeft } from 'lucide-svelte';
	import type {
		Diagram,
		DiagramSystem,
		ComponentLibraryItem,
	} from '$lib/types';

	let {
		data,
	}: {
		data: {
			diagram: Diagram;
			components: ComponentLibraryItem[];
			supabase: import('@supabase/supabase-js').SupabaseClient;
			session: { access_token?: string } | null;
		};
	} = $props();

	let addSystemOpen = $state(false);
	let saveStatus = $state<'idle' | 'dirty' | 'saving' | 'saved' | 'error'>('idle');

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
	}
</script>

<div class="flex flex-1 flex-col overflow-hidden">
	<!-- Header bar -->
	<div class="flex shrink-0 items-center justify-between border-b px-4 py-2">
		<div class="flex items-center gap-3">
			<Button variant="ghost" size="icon" onclick={() => goto('/diagrams')}>
				<ArrowLeft class="size-4" />
			</Button>
			<div>
				<h1 class="text-lg font-semibold">
					{diagramStore.currentDiagram?.customer_name ?? 'Diagram'}
				</h1>
				{#if diagramStore.currentDiagram?.title && diagramStore.currentDiagram.title !== diagramStore.currentDiagram.customer_name}
					<p class="text-muted-foreground text-sm">{diagramStore.currentDiagram.title}</p>
				{/if}
			</div>
		</div>
		<SaveStatusIndicator status={saveStatus} />
	</div>

	<!-- Body: sidebar + preview -->
	<div class="flex flex-1 overflow-hidden">
		<!-- Sidebar -->
		<div class="flex w-[360px] shrink-0 flex-col overflow-hidden border-r">
			<BuilderSidebar
				componentLibrary={diagramStore.componentLibrary}
				onAddCustom={() => (addSystemOpen = true)}
			/>
		</div>

		<!-- Preview -->
		<div class="flex-1 overflow-hidden p-4">
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
	</div>
</div>

<AddCustomSystemDialog
	bind:open={addSystemOpen}
	onsubmit={handleAddSystem}
	supabase={data.supabase}
	accessToken={data.session?.access_token}
/>
