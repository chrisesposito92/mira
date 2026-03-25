<script lang="ts">
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { Eye, EyeOff } from 'lucide-svelte';
	import { diagramStore } from '$lib/stores';
	import type { DiagramSettings } from '$lib/types';

	// eslint-disable-next-line svelte/prefer-writable-derived -- intentional: bgColor needs two-way binding with Input
	let bgColor = $state(diagramStore.currentDiagram?.content.settings.background_color ?? '#1a1f36');
	let bgError = $state('');

	// Rehydrate from store when diagram loads (component may mount before store is populated)
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

	// eslint-disable-next-line svelte/prefer-writable-derived -- needs two-way: user toggle + store rehydration
	let showLabels = $state(diagramStore.currentDiagram?.content.settings.show_labels ?? true);

	// Rehydrate showLabels from store when diagram loads
	$effect(() => {
		showLabels = diagramStore.currentDiagram?.content.settings.show_labels ?? true;
	});

	function toggleShowLabels() {
		showLabels = !showLabels;
		updateSettings({ show_labels: showLabels });
	}
</script>

<div class="space-y-6">
	<!-- Background Color -->
	<div class="space-y-1.5">
		<Label class="text-sm font-semibold">Background Color</Label>
		<div class="flex items-center gap-2">
			<div class="size-8 shrink-0 rounded border" style="background-color: {bgColor};"></div>
			<Input bind:value={bgColor} placeholder="#1a1f36" onblur={handleBgBlur} class="font-mono" />
		</div>
		{#if bgError}
			<p class="text-destructive text-xs">{bgError}</p>
		{/if}
	</div>

	<!-- Show Connection Labels -->
	<div class="space-y-1.5">
		<Label class="text-sm font-semibold">Show Connection Labels</Label>
		<Button
			variant={showLabels ? 'default' : 'outline'}
			size="sm"
			class="gap-1.5"
			onclick={toggleShowLabels}
		>
			{#if showLabels}
				<Eye class="size-3.5" />
				Visible
			{:else}
				<EyeOff class="size-3.5" />
				Hidden
			{/if}
		</Button>
	</div>
</div>
