<script lang="ts">
	import { Button } from '$lib/components/ui/button';

	let {
		icon,
		title,
		description,
		actionLabel,
		onaction,
	}: {
		// eslint-disable-next-line @typescript-eslint/no-explicit-any -- lucide-svelte uses Svelte 4 class types
		icon?: new (...args: any[]) => any;
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
		<div class="bg-muted mb-4 rounded-full p-3">
			<svelte:component this={icon} class="text-muted-foreground size-6" />
		</div>
	{/if}
	<h3 class="text-lg font-semibold">{title}</h3>
	<p class="text-muted-foreground mt-1 max-w-sm text-sm">{description}</p>
	{#if actionLabel && onaction}
		<Button class="mt-4" onclick={onaction}>{actionLabel}</Button>
	{/if}
</div>
