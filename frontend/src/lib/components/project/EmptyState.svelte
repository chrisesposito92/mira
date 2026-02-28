<script lang="ts">
	import { Button } from '$lib/components/ui/button';

	import type { Component, SvelteComponent } from 'svelte';

	// lucide-svelte exports Svelte 4 class components — accept both Svelte 4 + 5 types
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	type AnyComponent = Component<{ class?: string }> | (new (...args: any[]) => SvelteComponent);

	let {
		icon,
		title,
		description,
		actionLabel,
		onaction,
	}: {
		icon?: AnyComponent;
		title: string;
		description: string;
		actionLabel?: string;
		onaction?: () => void;
	} = $props();
</script>

<div
	class="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center"
>
	{#if icon}
		{@const Icon = icon}
		<div class="bg-muted mb-4 rounded-full p-3">
			<Icon class="text-muted-foreground size-6" />
		</div>
	{/if}
	<h3 class="text-lg font-semibold">{title}</h3>
	<p class="text-muted-foreground mt-1 max-w-sm text-sm">{description}</p>
	{#if actionLabel && onaction}
		<Button class="mt-4" onclick={onaction}>{actionLabel}</Button>
	{/if}
</div>
