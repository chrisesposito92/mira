<script lang="ts">
	import { page } from '$app/state';
	import * as Sidebar from '$lib/components/ui/sidebar';
	import { LayoutDashboard, FolderKanban, Building2 } from 'lucide-svelte';
	import { authStore } from '$lib/stores';

	const navItems = [
		{ title: 'Dashboard', url: '/dashboard', icon: LayoutDashboard },
		{ title: 'Projects', url: '/projects', icon: FolderKanban },
		{ title: 'Org Connections', url: '/orgs', icon: Building2 }
	];

	function isActive(url: string): boolean {
		return page.url.pathname === url || page.url.pathname.startsWith(url + '/');
	}
</script>

<Sidebar.Root>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton class="h-10 font-bold tracking-tight">
					MIRA
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>

	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each navItems as item}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton
								isActive={isActive(item.url)}
							>
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
						class="flex size-6 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground"
					>
						{authStore.userInitials}
					</div>
					<span class="truncate text-muted-foreground">{authStore.displayName}</span>
				</div>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Footer>

	<Sidebar.Rail />
</Sidebar.Root>
