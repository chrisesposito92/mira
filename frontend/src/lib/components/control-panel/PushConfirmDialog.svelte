<script lang="ts">
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import { Button } from '$lib/components/ui/button';
	import { snakeToTitle } from '$lib/utils.js';
	import type { GeneratedObject } from '$lib/types';

	let {
		open = $bindable(false),
		objects = [],
		pushing = false,
		onconfirm,
		oncancel,
	}: {
		open: boolean;
		objects: GeneratedObject[];
		pushing: boolean;
		onconfirm: () => void;
		oncancel: () => void;
	} = $props();

	// Group objects by entity type with counts
	const groupedCounts = $derived.by(() => {
		const counts: Record<string, number> = {};
		for (const obj of objects) {
			counts[obj.entity_type] = (counts[obj.entity_type] ?? 0) + 1;
		}
		return Object.entries(counts).map(([type, count]) => ({
			type,
			label: snakeToTitle(type),
			count,
		}));
	});
</script>

<AlertDialog.Root bind:open>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Push to m3ter</AlertDialog.Title>
			<AlertDialog.Description>
				You are about to push {objects.length} object{objects.length !== 1 ? 's' : ''} to m3ter.
			</AlertDialog.Description>
		</AlertDialog.Header>

		<div class="space-y-3 py-2">
			<!-- Entity type breakdown -->
			<div class="space-y-1">
				{#each groupedCounts as group (group.type)}
					<div class="flex items-center justify-between text-sm">
						<span>{group.label}</span>
						<span class="text-muted-foreground">{group.count}</span>
					</div>
				{/each}
			</div>

			<!-- Warning -->
			<p class="text-muted-foreground text-sm">
				Objects will be pushed in dependency order. If one fails, remaining objects will not be
				pushed.
			</p>
		</div>

		<AlertDialog.Footer>
			<AlertDialog.Cancel onclick={oncancel}>Cancel</AlertDialog.Cancel>
			<Button
				class="bg-green-600 text-white hover:bg-green-700"
				disabled={pushing}
				onclick={onconfirm}
			>
				{pushing ? 'Pushing...' : `Push ${objects.length} Object${objects.length !== 1 ? 's' : ''}`}
			</Button>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
