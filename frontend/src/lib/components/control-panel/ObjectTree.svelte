<script lang="ts">
	import { ChevronRight, ChevronDown } from 'lucide-svelte';
	import { Badge } from '$lib/components/ui/badge';
	import { snakeToTitle } from '$lib/utils.js';
	import ObjectTreeNode from './ObjectTreeNode.svelte';
	import type { EntityGroup } from '$lib/stores/objects.svelte.js';

	let {
		tree,
		selectedObjectId = null,
		selectedIds = new Set<string>(),
		onselect,
		ontoggle,
	}: {
		tree: EntityGroup[];
		selectedObjectId: string | null;
		selectedIds: Set<string>;
		onselect: (id: string) => void;
		ontoggle: (id: string) => void;
	} = $props();

	// Track expanded/collapsed state per entity type — all expanded by default
	let expanded = $state<Record<string, boolean>>({});

	// Initialize expanded state when tree changes
	$effect(() => {
		for (const group of tree) {
			if (!(group.entityType in expanded)) {
				expanded[group.entityType] = true;
			}
		}
	});

	function toggleGroup(entityType: string) {
		expanded[entityType] = !expanded[entityType];
	}
</script>

<div class="overflow-y-auto">
	{#each tree as group (group.entityType)}
		<div class="mb-1">
			<button
				class="hover:bg-accent flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium"
				onclick={() => toggleGroup(group.entityType)}
			>
				{#if expanded[group.entityType]}
					<ChevronDown class="size-4 shrink-0" />
				{:else}
					<ChevronRight class="size-4 shrink-0" />
				{/if}
				<span class="flex-1 text-left">{snakeToTitle(group.entityType)}</span>
				<Badge variant="secondary" class="text-xs">{group.objects.length}</Badge>
			</button>

			{#if expanded[group.entityType]}
				<div class="ml-4">
					{#each group.objects as object (object.id)}
						<ObjectTreeNode
							{object}
							isSelected={selectedIds.has(object.id)}
							isActive={object.id === selectedObjectId}
							{onselect}
							{ontoggle}
						/>
					{/each}
				</div>
			{/if}
		</div>
	{/each}

	{#if tree.length === 0}
		<div class="text-muted-foreground flex items-center justify-center p-8 text-sm">
			No objects found
		</div>
	{/if}
</div>
