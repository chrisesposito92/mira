<script lang="ts">
	import { authStore } from '$lib/stores';
</script>

<div>
	<h1 class="text-2xl font-bold tracking-tight">Dashboard</h1>
	<p class="text-muted-foreground mt-2">
		Welcome back{authStore.displayName ? `, ${authStore.displayName}` : ''}.
	</p>
</div>
