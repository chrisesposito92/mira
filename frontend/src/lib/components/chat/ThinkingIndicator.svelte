<script lang="ts">
	import { snakeToTitle } from '$lib/utils.js';

	let { step = '' }: { step?: string } = $props();
</script>

<div class="flex items-center gap-3 px-4 py-3">
	<div class="flex gap-1">
		<span class="bg-muted-foreground size-2 animate-bounce rounded-full [animation-delay:0ms]"
		></span>
		<span class="bg-muted-foreground size-2 animate-bounce rounded-full [animation-delay:150ms]"
		></span>
		<span class="bg-muted-foreground size-2 animate-bounce rounded-full [animation-delay:300ms]"
		></span>
	</div>
	{#if step}
		<span class="text-muted-foreground text-sm">
			{snakeToTitle(step)}...
		</span>
	{/if}
</div>
