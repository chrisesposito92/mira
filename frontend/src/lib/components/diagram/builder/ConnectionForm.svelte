<script lang="ts">
	import * as Select from '$lib/components/ui/select';
	import * as ToggleGroup from '$lib/components/ui/toggle-group';
	import { Switch } from '$lib/components/ui/switch';
	import { Input } from '$lib/components/ui/input';
	import { Button } from '$lib/components/ui/button';
	import { Label } from '$lib/components/ui/label';
	import { diagramStore } from '$lib/stores';
	import { HUB_ENDPOINT, getSuggestionsForSystem } from './suggestions.js';
	import type { DiagramConnection, DiagramSystem, ComponentLibraryItem } from '$lib/types';

	let {
		systems,
		componentLibrary,
		editingConnection = null,
		onsubmit,
		oncancel,
	}: {
		systems: DiagramSystem[];
		componentLibrary: ComponentLibraryItem[];
		editingConnection?: DiagramConnection | null;
		onsubmit: (connection: DiagramConnection) => void;
		oncancel: () => void;
	} = $props();

	let sourceId = $state<string>(editingConnection?.source_id ?? '');
	let targetId = $state<string>(editingConnection?.target_id ?? '');
	let direction = $state<'unidirectional' | 'bidirectional'>(
		editingConnection?.direction ?? 'unidirectional',
	);
	let connectionType = $state<DiagramConnection['connection_type']>(
		editingConnection?.connection_type ?? 'api',
	);
	let label = $state<string>(editingConnection?.label ?? '');
	let userHasChangedType = $state(false);
	let errors = $state<Record<string, string>>({});

	// Build connectable endpoints: hub + all systems from content.systems
	const connectableEndpoints = $derived.by(() => {
		const hubEntry = { id: HUB_ENDPOINT.id, name: HUB_ENDPOINT.name };
		const systemEntries = systems.map((s) => ({ id: s.id, name: s.name }));
		return [hubEntry, ...systemEntries];
	});

	// Target options exclude the selected source
	const targetEndpoints = $derived(connectableEndpoints.filter((e) => e.id !== sourceId));

	// Re-initialize form when editingConnection changes
	$effect(() => {
		if (editingConnection) {
			sourceId = editingConnection.source_id;
			targetId = editingConnection.target_id;
			direction = editingConnection.direction;
			connectionType = editingConnection.connection_type;
			label = editingConnection.label;
			userHasChangedType = true;
		}
	});

	// Reset userHasChangedType when source/target changes (BEFORE auto-suggest)
	$effect(() => {
		const _s = sourceId;
		const _t = targetId;
		userHasChangedType = false;
	});

	// CONN-06: Auto-suggest native_connector when hub is connected to a native connector system
	$effect(() => {
		if (!sourceId || !targetId) return;
		if (userHasChangedType) return;

		const isSourceHub = sourceId === 'hub';
		const isTargetHub = targetId === 'hub';

		if (isSourceHub || isTargetHub) {
			const otherId = isSourceHub ? targetId : sourceId;
			const otherSystem = systems.find((s) => s.id === otherId);
			if (!otherSystem) return;

			const libItem = componentLibrary.find((c) => c.id === otherSystem.component_library_id);
			if (libItem?.is_native_connector) {
				connectionType = 'native_connector';
			}
		}
	});

	// Label suggestions based on source system's category
	const labelSuggestions = $derived.by(() => {
		if (!sourceId) return [];
		if (sourceId === 'hub') return getSuggestionsForSystem(null);
		const system = systems.find((s) => s.id === sourceId);
		return getSuggestionsForSystem(system?.category ?? null);
	});

	const filteredSuggestions = $derived(
		label.length === 0
			? labelSuggestions
			: labelSuggestions.filter((s) => s.toLowerCase().includes(label.toLowerCase())),
	);

	function validate(): boolean {
		errors = {};
		if (!sourceId) errors.source = 'Select a source system';
		if (!targetId) errors.target = 'Select a target system';
		if (sourceId && targetId && sourceId === targetId) {
			errors.target = 'Source and target must be different systems';
		}
		if (label.length > 60) errors.label = 'Label must be 60 characters or fewer';
		const existing = diagramStore.currentDiagram?.content.connections ?? [];
		const isDuplicate = existing.some(
			(c) =>
				c.id !== editingConnection?.id &&
				((c.source_id === sourceId && c.target_id === targetId) ||
					(c.source_id === targetId && c.target_id === sourceId)) &&
				c.label === label,
		);
		if (isDuplicate) errors.duplicate = 'This exact connection already exists';
		return Object.keys(errors).length === 0;
	}

	function handleSubmit() {
		if (!validate()) return;
		const connection: DiagramConnection = {
			id: editingConnection?.id ?? crypto.randomUUID(),
			source_id: sourceId,
			target_id: targetId,
			label,
			direction,
			connection_type: connectionType,
		};
		onsubmit(connection);
	}

	const TYPE_LABELS: Record<DiagramConnection['connection_type'], string> = {
		native_connector: 'Native',
		webhook_api: 'Webhook',
		custom_build: 'Custom',
		api: 'API',
	};
</script>

<div class="space-y-4">
	<!-- Source -->
	<div class="space-y-1.5">
		<Label>Source</Label>
		<Select.Root type="single" bind:value={sourceId}>
			<Select.Trigger>
				{connectableEndpoints.find((e) => e.id === sourceId)?.name ?? 'Select source'}
			</Select.Trigger>
			<Select.Content>
				{#each connectableEndpoints as endpoint (endpoint.id)}
					<Select.Item value={endpoint.id}>{endpoint.name}</Select.Item>
				{/each}
			</Select.Content>
		</Select.Root>
		{#if errors.source}
			<p class="text-destructive text-xs">{errors.source}</p>
		{/if}
	</div>

	<!-- Target -->
	<div class="space-y-1.5">
		<Label>Target</Label>
		<Select.Root type="single" bind:value={targetId}>
			<Select.Trigger>
				{targetEndpoints.find((e) => e.id === targetId)?.name ?? 'Select target'}
			</Select.Trigger>
			<Select.Content>
				{#each targetEndpoints as endpoint (endpoint.id)}
					<Select.Item value={endpoint.id}>{endpoint.name}</Select.Item>
				{/each}
			</Select.Content>
		</Select.Root>
		{#if errors.target}
			<p class="text-destructive text-xs">{errors.target}</p>
		{/if}
	</div>

	<!-- Direction -->
	<div class="flex items-center justify-between">
		<Label>{direction === 'bidirectional' ? 'Two-way' : 'One-way'}</Label>
		<Switch
			checked={direction === 'bidirectional'}
			onCheckedChange={(checked) => {
				direction = checked ? 'bidirectional' : 'unidirectional';
			}}
		/>
	</div>

	<!-- Integration Type -->
	<div class="space-y-1.5">
		<Label>Integration Type</Label>
		<ToggleGroup.Root
			type="single"
			bind:value={connectionType}
			onValueChange={() => {
				userHasChangedType = true;
			}}
			class="w-full"
			variant="outline"
		>
			{#each Object.entries(TYPE_LABELS) as [value, text] (value)}
				<ToggleGroup.Item {value} class="flex-1 text-xs">{text}</ToggleGroup.Item>
			{/each}
		</ToggleGroup.Root>
	</div>

	<!-- Label -->
	<div class="space-y-1.5">
		<div class="flex items-center justify-between">
			<Label>Label</Label>
			<span class="text-muted-foreground text-xs">{label.length}/60</span>
		</div>
		<Input bind:value={label} placeholder="e.g. Usage Events" maxlength={60} />
		{#if filteredSuggestions.length > 0 && label.length < 60}
			<div class="flex flex-wrap gap-1 pt-1">
				{#each filteredSuggestions as suggestion (suggestion)}
					<button
						type="button"
						class="bg-muted hover:bg-accent rounded-md px-2 py-0.5 text-xs transition-colors"
						onclick={() => (label = suggestion)}
					>
						{suggestion}
					</button>
				{/each}
			</div>
		{/if}
		{#if errors.label}
			<p class="text-destructive text-xs">{errors.label}</p>
		{/if}
		{#if errors.duplicate}
			<p class="text-destructive text-xs">{errors.duplicate}</p>
		{/if}
	</div>

	<!-- Actions -->
	<div class="flex gap-2">
		<Button class="flex-1" onclick={handleSubmit}>
			{editingConnection ? 'Update Connection' : 'Add Connection'}
		</Button>
		<Button variant="outline" onclick={oncancel}>Discard Changes</Button>
	</div>
</div>
