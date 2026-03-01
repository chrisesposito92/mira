<script lang="ts">
	import StatusBadge from '$lib/components/project/StatusBadge.svelte';
	import { Loader2 } from 'lucide-svelte';
	import { cn } from '$lib/utils.js';
	import type { GeneratedObject } from '$lib/types';

	let {
		object,
		isSelected = false,
		isActive = false,
		isPushing = false,
		onselect,
		ontoggle,
	}: {
		object: GeneratedObject;
		isSelected: boolean;
		isActive: boolean;
		isPushing?: boolean;
		onselect: (id: string) => void;
		ontoggle: (id: string) => void;
	} = $props();

	const displayName = $derived(object.name || object.code || 'Untitled');
</script>

<button
	class={cn(
		'hover:bg-accent flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm',
		isActive && 'bg-accent',
	)}
	onclick={() => onselect(object.id)}
>
	<input
		type="checkbox"
		checked={isSelected}
		onclick={(e) => {
			e.stopPropagation();
			ontoggle(object.id);
		}}
		class="border-muted-foreground size-3.5 rounded"
	/>
	<span class="flex-1 truncate">{displayName}</span>
	{#if isPushing}
		<Loader2 class="size-4 animate-spin text-blue-500" />
	{:else}
		<StatusBadge status={object.status} class="text-xs" />
	{/if}
</button>
