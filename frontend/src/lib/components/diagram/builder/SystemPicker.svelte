<script lang="ts">
	import * as Collapsible from '$lib/components/ui/collapsible';
	import * as ScrollArea from '$lib/components/ui/scroll-area';
	import { Input } from '$lib/components/ui/input';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { ChevronDown, Plus, X } from 'lucide-svelte';
	import { SvelteMap } from 'svelte/reactivity';
	import { diagramStore } from '$lib/stores';
	import { snakeToTitle } from '$lib/utils.js';
	import SystemPickerItem from './SystemPickerItem.svelte';
	import type { ComponentLibraryItem, DiagramSystem } from '$lib/types';

	let {
		componentLibrary,
		onAddCustom,
	}: {
		componentLibrary: ComponentLibraryItem[];
		onAddCustom: () => void;
	} = $props();

	let searchQuery = $state('');

	const filteredGroups = $derived.by(() => {
		const query = searchQuery.toLowerCase();
		const filtered = componentLibrary.filter((item) => item.name.toLowerCase().includes(query));
		const groups = new SvelteMap<string, ComponentLibraryItem[]>();
		for (const item of filtered.sort((a, b) => a.display_order - b.display_order)) {
			const existing = groups.get(item.category) ?? [];
			existing.push(item);
			groups.set(item.category, existing);
		}
		return groups;
	});

	const addedSystemIds = $derived(
		new Set(
			(diagramStore.currentDiagram?.content.systems ?? [])
				.filter((s) => s.component_library_id)
				.map((s) => s.component_library_id!),
		),
	);

	const currentSystems = $derived(
		(diagramStore.currentDiagram?.content.systems ?? []).filter(
			(s) => s.role !== 'hub' && s.role !== 'prospect',
		),
	);

	function handleAddSystem(item: ComponentLibraryItem) {
		const system: DiagramSystem = {
			id: crypto.randomUUID(),
			component_library_id: item.id,
			name: item.name,
			logo_base64: item.logo_base64,
			x: 0,
			y: 0,
			category: item.category,
			role: 'system',
		};
		diagramStore.addSystem(system);
	}
</script>

<div class="flex h-full flex-col">
	<!-- Search -->
	<div class="shrink-0 p-3">
		<search aria-label="Search systems">
			<Input placeholder="Search systems..." bind:value={searchQuery} class="h-9" />
		</search>
	</div>

	<!-- Scrollable content -->
	<ScrollArea.Root class="flex-1">
		<div class="space-y-1 px-3 pb-3">
			<!-- Current Systems (removable) -->
			{#if currentSystems.length > 0}
				<div class="mb-3">
					<p
						class="text-muted-foreground mb-1.5 px-2 text-xs font-semibold tracking-wider uppercase"
					>
						Current Systems
					</p>
					{#each currentSystems as system (system.id)}
						<div class="flex items-center gap-2 rounded-md px-2 py-1">
							{#if system.logo_base64}
								<img src={system.logo_base64} alt="" class="size-5 shrink-0 rounded" />
							{:else}
								<span class="bg-muted size-5 shrink-0 rounded"></span>
							{/if}
							<span class="flex-1 truncate text-sm">{system.name}</span>
							<button
								type="button"
								class="text-muted-foreground hover:text-foreground shrink-0 rounded p-0.5 transition-colors"
								aria-label="Remove {system.name}"
								onclick={() => diagramStore.removeSystem(system.id)}
							>
								<X class="size-3.5" />
							</button>
						</div>
					{/each}
				</div>
			{/if}

			<!-- Category Accordion -->
			{#each [...filteredGroups.entries()] as [category, items] (category)}
				<Collapsible.Root open={true}>
					<Collapsible.Trigger
						class="hover:bg-accent flex w-full items-center gap-2 rounded-md px-2 py-1.5 transition-colors"
					>
						<ChevronDown
							class="size-4 shrink-0 transition-transform [[data-state=closed]>&]:rotate-[-90deg]"
						/>
						<span class="text-sm font-semibold">{snakeToTitle(category)}</span>
						<Badge variant="secondary" class="ml-auto text-xs">{items.length}</Badge>
					</Collapsible.Trigger>
					<Collapsible.Content>
						<div class="ml-2 space-y-0.5 py-1">
							{#each items as item (item.id)}
								<SystemPickerItem
									{item}
									isAdded={addedSystemIds.has(item.id)}
									onclick={() => handleAddSystem(item)}
								/>
							{/each}
						</div>
					</Collapsible.Content>
				</Collapsible.Root>
			{/each}

			<!-- Add Custom System button -->
			<div class="pt-2">
				<Button variant="outline" class="w-full gap-2" onclick={onAddCustom}>
					<Plus class="size-4" />
					Add Custom System
				</Button>
			</div>
		</div>
	</ScrollArea.Root>
</div>
