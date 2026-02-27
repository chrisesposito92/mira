<script lang="ts">
	import { authStore } from '$lib/stores';
</script>

<div>
	<h1 class="text-2xl font-bold tracking-tight">Dashboard</h1>
	<p class="mt-2 text-muted-foreground">
		Welcome back{authStore.displayName ? `, ${authStore.displayName}` : ''}.
	</p>
</div>
