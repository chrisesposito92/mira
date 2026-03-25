<script lang="ts">
	import type { ComponentLibraryItem } from '$lib/types';

	let {
		componentLibrary,
		onAddCustom,
	}: {
		componentLibrary: ComponentLibraryItem[];
		onAddCustom: () => void;
	} = $props();
</script>

<!-- Placeholder — full implementation in Task 2 -->
<div class="flex h-full flex-col p-4">
	<p class="text-muted-foreground text-sm">Builder sidebar loading...</p>
</div>
