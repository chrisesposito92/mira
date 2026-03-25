<script lang="ts">
	import { Check } from 'lucide-svelte';
	import { cn } from '$lib/utils.js';
	import type { ComponentLibraryItem } from '$lib/types';

	let {
		item,
		isAdded,
		onclick,
	}: {
		item: ComponentLibraryItem;
		isAdded: boolean;
		onclick: () => void;
	} = $props();
</script>

<button
	type="button"
	class={cn(
		'flex w-full items-center gap-3 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
		isAdded ? 'cursor-default opacity-50' : 'hover:bg-accent cursor-pointer',
	)}
	disabled={isAdded}
	aria-disabled={isAdded}
	onclick={() => {
		if (!isAdded) onclick();
	}}
>
	{#if item.logo_base64}
		<img src={item.logo_base64} alt="" class="size-5 shrink-0 rounded" />
	{:else}
		<span class="bg-muted size-5 shrink-0 rounded"></span>
	{/if}
	<span class="flex-1 truncate text-sm">{item.name}</span>
	{#if isAdded}
		<Check class="text-muted-foreground size-4 shrink-0" />
	{/if}
</button>
