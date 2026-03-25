<script lang="ts">
	import * as Tabs from '$lib/components/ui/tabs';
	import { Blocks, Cable, Settings as SettingsIcon } from 'lucide-svelte';
	import SystemPicker from './SystemPicker.svelte';
	import type { ComponentLibraryItem } from '$lib/types';

	let {
		componentLibrary,
		onAddCustom,
	}: {
		componentLibrary: ComponentLibraryItem[];
		onAddCustom: () => void;
	} = $props();
</script>

<Tabs.Root value="systems" class="flex h-full flex-col">
	<Tabs.List class="w-full shrink-0 justify-start rounded-none border-b px-4">
		<Tabs.Trigger value="systems" class="gap-1.5">
			<Blocks class="size-4" />
			<span class="text-xs">Systems</span>
		</Tabs.Trigger>
		<Tabs.Trigger value="connections" class="gap-1.5">
			<Cable class="size-4" />
			<span class="text-xs">Connections</span>
		</Tabs.Trigger>
		<Tabs.Trigger value="settings" class="gap-1.5">
			<SettingsIcon class="size-4" />
			<span class="text-xs">Settings</span>
		</Tabs.Trigger>
	</Tabs.List>
	<Tabs.Content value="systems" class="mt-0 flex-1 overflow-hidden p-0">
		<SystemPicker {componentLibrary} {onAddCustom} />
	</Tabs.Content>
	<Tabs.Content value="connections" class="mt-0 flex-1 overflow-hidden p-4">
		<!-- ConnectionForm + ConnectionList from Plan 03 -->
		<p class="text-muted-foreground text-sm">Connections tab - coming soon</p>
	</Tabs.Content>
	<Tabs.Content value="settings" class="mt-0 flex-1 overflow-hidden p-4">
		<!-- SettingsPanel from Plan 03 -->
		<p class="text-muted-foreground text-sm">Settings tab - coming soon</p>
	</Tabs.Content>
</Tabs.Root>
