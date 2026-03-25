<script lang="ts">
	import { Check, Loader2, AlertTriangle, Circle } from 'lucide-svelte';

	let {
		status,
	}: {
		status: 'idle' | 'dirty' | 'saving' | 'saved' | 'error';
	} = $props();

	let showSaved = $state(true);

	$effect(() => {
		if (status === 'saved') {
			showSaved = true;
			const timer = setTimeout(() => {
				showSaved = false;
			}, 2000);
			return () => clearTimeout(timer);
		}
	});
</script>

<span class="flex items-center gap-1.5" aria-live="polite">
	{#if status === 'idle'}
		<span></span>
	{:else if status === 'dirty'}
		<Circle class="text-muted-foreground size-2 fill-current" />
	{:else if status === 'saving'}
		<Loader2 class="text-muted-foreground size-3.5 animate-spin" />
		<span class="text-muted-foreground text-xs">Saving...</span>
	{:else if status === 'saved'}
		<span
			class="flex items-center gap-1.5 transition-opacity duration-1000"
			class:opacity-0={!showSaved}
		>
			<Check class="size-3.5 text-green-500" />
			<span class="text-muted-foreground text-xs">Saved</span>
		</span>
	{:else if status === 'error'}
		<AlertTriangle class="text-destructive size-3.5" />
		<span class="text-destructive text-xs">Save failed</span>
	{/if}
</span>
