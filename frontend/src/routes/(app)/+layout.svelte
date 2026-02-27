<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar';
	import { AppSidebar, AppHeader } from '$lib/components/layout';
	import { authStore } from '$lib/stores';

	let { data, children } = $props();

	$effect(() => {
		authStore.set(data.session, data.user);
	});
</script>

<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset>
		<AppHeader />
		<main class="flex-1 p-6">
			{@render children()}
		</main>
	</Sidebar.Inset>
</Sidebar.Provider>
