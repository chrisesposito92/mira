<script lang="ts">
	import { untrack } from 'svelte';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Switch } from '$lib/components/ui/switch';
	import { diagramStore } from '$lib/stores';
	import type { DiagramSettings } from '$lib/types';

	let bgColor = $state(diagramStore.currentDiagram?.content.settings.background_color ?? '#1a1f36');
	let bgError = $state('');

	$effect(() => {
		bgColor = diagramStore.currentDiagram?.content.settings.background_color ?? '#1a1f36';
	});

	function updateSettings(updates: Partial<DiagramSettings>) {
		if (!diagramStore.currentDiagram) return;
		diagramStore.currentDiagram = {
			...diagramStore.currentDiagram,
			content: {
				...diagramStore.currentDiagram.content,
				settings: {
					...diagramStore.currentDiagram.content.settings,
					...updates,
				},
			},
		};
	}

	function handleBgBlur() {
		const hex = /^#[0-9a-fA-F]{6}$/;
		if (!hex.test(bgColor)) {
			bgError = 'Enter a valid hex color (e.g., #1a1f36)';
			return;
		}
		bgError = '';
		updateSettings({ background_color: bgColor });
	}

	let showLabels = $state(
		diagramStore.currentDiagram?.content.settings.show_labels ?? true,
	);

	// Sync showLabels toggle with store — untrack store reads to prevent infinite loop
	let showLabelsInit = false;
	$effect(() => {
		const val = showLabels;
		if (!showLabelsInit) {
			showLabelsInit = true;
			return;
		}
		untrack(() => {
			updateSettings({ show_labels: val });
		});
	});
</script>

<div class="space-y-6">
	<!-- Background Color -->
	<div class="space-y-1.5">
		<Label class="text-sm font-semibold">Background Color</Label>
		<div class="flex items-center gap-2">
			<div
				class="size-8 shrink-0 rounded border"
				style="background-color: {bgColor};"
			></div>
			<Input bind:value={bgColor} placeholder="#1a1f36" onblur={handleBgBlur} class="font-mono" />
		</div>
		{#if bgError}
			<p class="text-destructive text-xs">{bgError}</p>
		{/if}
	</div>

	<!-- Show Connection Labels -->
	<div class="flex items-center justify-between">
		<Label class="text-sm font-semibold">Show Connection Labels</Label>
		<Switch bind:checked={showLabels} />
	</div>
</div>
