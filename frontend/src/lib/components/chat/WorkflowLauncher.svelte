<script lang="ts">
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Play } from 'lucide-svelte';
	import { cn } from '$lib/utils.js';
	import type { LlmModel, Workflow, WorkflowType } from '$lib/types/workflow.js';

	let {
		models,
		workflows = [],
		loading = false,
		onstart,
	}: {
		models: LlmModel[];
		workflows?: Workflow[];
		loading?: boolean;
		onstart?: (modelId: string, workflowType: WorkflowType) => void | Promise<void>;
	} = $props();

	let selectedModelId = $state('');
	let selectedWorkflowType = $state<WorkflowType>('product_meter_aggregation');

	const selectedLabel = $derived(
		models.find((m) => m.id === selectedModelId)?.display_name || 'Select a model...',
	);

	const hasCompletedWf1 = $derived(
		workflows.some(
			(w) => w.workflow_type === 'product_meter_aggregation' && w.status === 'completed',
		),
	);

	const hasCompletedWf2 = $derived(
		workflows.some((w) => w.workflow_type === 'plan_pricing' && w.status === 'completed'),
	);

	const hasCompletedWf3 = $derived(
		workflows.some((w) => w.workflow_type === 'account_setup' && w.status === 'completed'),
	);

	async function handleStart() {
		if (!selectedModelId || loading) return;
		await onstart?.(selectedModelId, selectedWorkflowType);
	}
</script>

<div class="flex flex-col items-center justify-center gap-6 py-16">
	<div class="text-center">
		<h2 class="text-lg font-semibold">Start Workflow</h2>
		<p class="text-muted-foreground mt-1 text-sm">Select a workflow type and AI model to begin.</p>
	</div>

	<!-- Workflow Type Selection -->
	<div class="flex w-full max-w-md flex-col gap-2">
		<button
			class={cn(
				'rounded-lg border p-4 text-left transition-colors',
				selectedWorkflowType === 'product_meter_aggregation'
					? 'border-primary bg-primary/5'
					: 'hover:border-muted-foreground/50',
			)}
			onclick={() => (selectedWorkflowType = 'product_meter_aggregation')}
		>
			<div class="font-medium">Products, Meters & Aggregations</div>
			<p class="text-muted-foreground mt-1 text-xs">Generate core m3ter billing entities</p>
		</button>

		<button
			class={cn(
				'rounded-lg border p-4 text-left transition-colors',
				!hasCompletedWf1
					? 'cursor-not-allowed opacity-50'
					: selectedWorkflowType === 'plan_pricing'
						? 'border-primary bg-primary/5'
						: 'hover:border-muted-foreground/50',
			)}
			onclick={() => {
				if (hasCompletedWf1) selectedWorkflowType = 'plan_pricing';
			}}
			disabled={!hasCompletedWf1}
		>
			<div class="font-medium">Plans & Pricing</div>
			<p class="text-muted-foreground mt-1 text-xs">
				{hasCompletedWf1
					? 'Generate plan templates, plans, and pricing'
					: 'Complete Workflow 1 first'}
			</p>
		</button>

		<button
			class={cn(
				'rounded-lg border p-4 text-left transition-colors',
				!hasCompletedWf2
					? 'cursor-not-allowed opacity-50'
					: selectedWorkflowType === 'account_setup'
						? 'border-primary bg-primary/5'
						: 'hover:border-muted-foreground/50',
			)}
			onclick={() => {
				if (hasCompletedWf2) selectedWorkflowType = 'account_setup';
			}}
			disabled={!hasCompletedWf2}
		>
			<div class="font-medium">Accounts & Account Plans</div>
			<p class="text-muted-foreground mt-1 text-xs">
				{hasCompletedWf2
					? 'Generate customer accounts and plan assignments'
					: 'Complete Workflow 2 first'}
			</p>
		</button>

		<button
			class={cn(
				'rounded-lg border p-4 text-left transition-colors',
				!hasCompletedWf3
					? 'cursor-not-allowed opacity-50'
					: selectedWorkflowType === 'usage_submission'
						? 'border-primary bg-primary/5'
						: 'hover:border-muted-foreground/50',
			)}
			onclick={() => {
				if (hasCompletedWf3) selectedWorkflowType = 'usage_submission';
			}}
			disabled={!hasCompletedWf3}
		>
			<div class="font-medium">Usage & Measurements</div>
			<p class="text-muted-foreground mt-1 text-xs">
				{hasCompletedWf3 ? 'Generate sample usage measurement data' : 'Complete Workflow 3 first'}
			</p>
		</button>
	</div>

	<!-- Model Selection + Start Button -->
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
