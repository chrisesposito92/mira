<script lang="ts">
	import * as Tabs from '$lib/components/ui/tabs';
	import { Separator } from '$lib/components/ui/separator';
	import { Button } from '$lib/components/ui/button';
	import { Blocks, Cable, Settings as SettingsIcon, Plus } from 'lucide-svelte';
	import { diagramStore } from '$lib/stores';
	import SystemPicker from './SystemPicker.svelte';
	import ConnectionForm from './ConnectionForm.svelte';
	import ConnectionList from './ConnectionList.svelte';
	import SettingsPanel from './SettingsPanel.svelte';
	import type { ComponentLibraryItem, DiagramConnection } from '$lib/types';

	let {
		componentLibrary,
		onAddCustom,
	}: {
		componentLibrary: ComponentLibraryItem[];
		onAddCustom: () => void;
	} = $props();

	let showConnectionForm = $state(false);
	let editingConnection = $state<DiagramConnection | null>(null);

	function handleConnectionSubmit(connection: DiagramConnection) {
		if (editingConnection) {
			diagramStore.updateConnection(connection.id, connection);
		} else {
			diagramStore.addConnection(connection);
		}
		showConnectionForm = false;
		editingConnection = null;
	}

	function handleEditConnection(connection: DiagramConnection) {
		editingConnection = connection;
		showConnectionForm = true;
	}

	function handleDeleteConnection(connectionId: string) {
		diagramStore.removeConnection(connectionId);
	}

	function handleCancelForm() {
		showConnectionForm = false;
		editingConnection = null;
	}
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
	<Tabs.Content value="connections" class="mt-0 flex-1 overflow-hidden p-0">
		<div class="flex h-full flex-col gap-3 p-4">
			{#if !showConnectionForm}
				<Button variant="outline" class="w-full gap-2" onclick={() => (showConnectionForm = true)}>
					<Plus class="size-4" />
					Add Connection
				</Button>
			{/if}
			{#if showConnectionForm}
				<ConnectionForm
					systems={diagramStore.currentDiagram?.content.systems ?? []}
					{componentLibrary}
					{editingConnection}
					onsubmit={handleConnectionSubmit}
					oncancel={handleCancelForm}
				/>
				<Separator />
			{/if}
			<ConnectionList
				connections={diagramStore.currentDiagram?.content.connections ?? []}
				systems={diagramStore.currentDiagram?.content.systems ?? []}
				onedit={handleEditConnection}
				ondelete={handleDeleteConnection}
			/>
		</div>
	</Tabs.Content>
	<Tabs.Content value="settings" class="mt-0 flex-1 overflow-hidden p-4">
		<SettingsPanel />
	</Tabs.Content>
</Tabs.Root>
