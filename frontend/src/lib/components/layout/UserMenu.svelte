<script lang="ts">
	import * as Avatar from '$lib/components/ui/avatar';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import { LogOut } from 'lucide-svelte';
	import { authStore } from '$lib/stores';
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger>
		<Avatar.Root class="size-8 cursor-pointer">
			<Avatar.Fallback class="text-xs">{authStore.userInitials}</Avatar.Fallback>
		</Avatar.Root>
	</DropdownMenu.Trigger>
	<DropdownMenu.Content align="end" class="w-56">
		<DropdownMenu.Label>
			<div class="flex flex-col">
				<span class="text-sm font-medium">{authStore.displayName}</span>
				<span class="text-muted-foreground text-xs">{authStore.user?.email ?? ''}</span>
			</div>
		</DropdownMenu.Label>
		<DropdownMenu.Separator />
		<form method="POST" action="/logout">
			<DropdownMenu.Item>
				{#snippet child({ props })}
					<button {...props} type="submit" class="flex w-full items-center">
						<LogOut class="mr-2 size-4" />
						Sign out
					</button>
				{/snippet}
			</DropdownMenu.Item>
		</form>
	</DropdownMenu.Content>
</DropdownMenu.Root>
