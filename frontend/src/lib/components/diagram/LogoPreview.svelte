<script lang="ts">
	import { Skeleton } from "$lib/components/ui/skeleton";

	let {
		logoBase64,
		loading,
		error,
	}: {
		logoBase64: string | null;
		loading: boolean;
		error: string | null;
	} = $props();
</script>

{#if loading}
	<div class="flex items-center gap-2">
		<Skeleton class="size-16 rounded-lg" />
		<p class="text-muted-foreground text-sm">Fetching logo...</p>
	</div>
{:else if error}
	<p class="text-muted-foreground text-sm">{error}</p>
{:else if logoBase64}
	<img src={logoBase64} alt="Logo preview" class="size-16 rounded-lg object-contain" />
{/if}
