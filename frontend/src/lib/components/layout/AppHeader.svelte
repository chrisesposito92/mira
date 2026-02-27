<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar';
	import { Separator } from '$lib/components/ui/separator';
	import { Breadcrumbs } from '$lib/components/layout';
	import ThemeToggle from './ThemeToggle.svelte';
	import UserMenu from './UserMenu.svelte';
</script>

<header class="flex h-14 shrink-0 items-center gap-2 border-b px-4">
	<Sidebar.Trigger class="-ml-1" />
	<Separator orientation="vertical" class="mr-2 !h-4" />
	<Breadcrumbs />
	<div class="ml-auto flex items-center gap-2">
		<ThemeToggle />
		<UserMenu />
	</div>
</header>
