<script lang="ts">
	import * as ScrollArea from '$lib/components/ui/scroll-area';
	import { Cable } from 'lucide-svelte';
	import ConnectionListItem from './ConnectionListItem.svelte';
	import type { DiagramConnection, DiagramSystem } from '$lib/types';

	let {
		connections,
		systems,
		onedit,
		ondelete,
	}: {
		connections: DiagramConnection[];
		systems: DiagramSystem[];
		onedit: (connection: DiagramConnection) => void;
		ondelete: (connectionId: string) => void;
	} = $props();

	function systemName(id: string): string {
		if (id === 'hub') return 'm3ter';
		return systems.find((s) => s.id === id)?.name ?? 'Unknown';
	}
</script>

{#if connections.length === 0}
	<div class="flex flex-col items-center gap-2 py-8 text-center">
		<Cable class="text-muted-foreground size-8" />
		<h3 class="text-sm font-semibold">No connections yet</h3>
		<p class="text-muted-foreground text-xs">
			Add a connection to define how systems exchange data.
		</p>
	</div>
{:else}
	<ScrollArea.Root class="max-h-[400px]">
		<div class="space-y-2">
			{#each connections as connection (connection.id)}
				<ConnectionListItem
					{connection}
					{systemName}
					onedit={() => onedit(connection)}
					ondelete={() => ondelete(connection.id)}
				/>
			{/each}
		</div>
	</ScrollArea.Root>
{/if}
