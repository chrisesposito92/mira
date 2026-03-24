<script lang="ts">
	import { page } from '$app/state';
	import * as Sidebar from '$lib/components/ui/sidebar';
	import { LayoutDashboard, FolderKanban, Network, Building2 } from 'lucide-svelte';
	import { authStore } from '$lib/stores';

	const navItems = [
		{ title: 'Dashboard', url: '/dashboard', icon: LayoutDashboard },
		{ title: 'Projects', url: '/projects', icon: FolderKanban },
		{ title: 'Diagrams', url: '/diagrams', icon: Network },
		{ title: 'Org Connections', url: '/orgs', icon: Building2 },
	];

	function isActive(item: (typeof navItems)[0]): boolean {
		const path = page.url.pathname;
		return path === item.url || path.startsWith(item.url + '/');
	}
</script>

<Sidebar.Root>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton class="h-10 font-bold tracking-tight">MIRA</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>

	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each navItems as item}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={isActive(item)}>
								{#snippet child({ props })}
									<a href={item.url} {...props}>
										<item.icon class="size-4" />
										<span>{item.title}</span>
									</a>
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
	</Sidebar.Content>

	<Sidebar.Footer>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<div class="flex items-center gap-2 px-2 py-1.5 text-sm">
					<div
						class="bg-primary text-primary-foreground flex size-6 items-center justify-center rounded-full text-[10px] font-medium"
					>
						{authStore.userInitials}
					</div>
					<span class="text-muted-foreground truncate">{authStore.displayName}</span>
				</div>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Footer>

	<Sidebar.Rail />
</Sidebar.Root>
