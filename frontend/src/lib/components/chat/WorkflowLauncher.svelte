<script lang="ts">
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Play } from 'lucide-svelte';
	import type { LlmModel } from '$lib/types/workflow.js';

	let {
		models,
		loading = false,
		onstart,
	}: {
		models: LlmModel[];
		loading?: boolean;
		onstart?: (modelId: string) => void | Promise<void>;
	} = $props();

	let selectedModelId = $state('');

	const selectedLabel = $derived(
		models.find((m) => m.id === selectedModelId)?.display_name || 'Select a model...',
	);

	async function handleStart() {
		if (!selectedModelId || loading) return;
		await onstart?.(selectedModelId);
	}
</script>

<div class="flex flex-col items-center justify-center gap-6 py-16">
	<div class="text-center">
		<h2 class="text-lg font-semibold">Start Workflow</h2>
		<p class="text-muted-foreground mt-1 text-sm">
			Select an AI model and start generating m3ter configurations.
		</p>
	</div>
	<div class="flex w-full max-w-sm flex-col gap-3">
		<Select.Root type="single" bind:value={selectedModelId}>
			<Select.Trigger>{selectedLabel}</Select.Trigger>
			<Select.Content>
				{#each models as model (model.id)}
					<Select.Item value={model.id}>{model.display_name}</Select.Item>
				{/each}
			</Select.Content>
		</Select.Root>
		<Button onclick={handleStart} disabled={!selectedModelId || loading}>
			<Play class="mr-2 size-4" />
			{loading ? 'Starting...' : 'Start Workflow'}
		</Button>
	</div>
</div>
