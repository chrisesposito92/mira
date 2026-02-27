<script lang="ts">
	let { children } = $props();
</script>

<div class="bg-background flex min-h-screen items-center justify-center">
	{@render children()}
</div>
