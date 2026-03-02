<script lang="ts">
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Play, Check } from 'lucide-svelte';
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
	let open = $state(false);

	const selectedModelLabel = $derived(
		models.find((m) => m.id === selectedModelId)?.display_name || 'Select model...',
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

	interface WfOption {
		type: WorkflowType;
		label: string;
		enabled: boolean;
		hint: string;
	}

	const workflowOptions = $derived<WfOption[]>([
		{
			type: 'product_meter_aggregation',
			label: 'Products, Meters & Aggregations',
			enabled: true,
			hint: 'Core billing entities',
		},
		{
			type: 'plan_pricing',
			label: 'Plans & Pricing',
			enabled: hasCompletedWf1,
			hint: hasCompletedWf1 ? 'Plan templates, plans, pricing' : 'Complete WF1 first',
		},
		{
			type: 'account_setup',
			label: 'Accounts & Account Plans',
			enabled: hasCompletedWf2,
			hint: hasCompletedWf2 ? 'Customer accounts' : 'Complete WF2 first',
		},
		{
			type: 'usage_submission',
			label: 'Usage & Measurements',
			enabled: hasCompletedWf3,
			hint: hasCompletedWf3 ? 'Sample usage data' : 'Complete WF3 first',
		},
	]);

	async function handleStart() {
		if (!selectedModelId || loading) return;
		open = false;
		await onstart?.(selectedModelId, selectedWorkflowType);
	}
</script>

<DropdownMenu.Root bind:open>
	<DropdownMenu.Trigger>
		{#snippet child({ props })}
			<Button size="sm" {...props}>
				<Play class="mr-1 size-4" />
				Run Workflow
			</Button>
		{/snippet}
	</DropdownMenu.Trigger>
	<DropdownMenu.Content class="w-72 p-3" align="end">
		<div class="space-y-3">
			<div class="space-y-1">
				<p class="text-muted-foreground text-xs font-medium">Workflow Type</p>
				{#each workflowOptions as opt (opt.type)}
					<button
						class={cn(
							'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
							!opt.enabled && 'cursor-not-allowed opacity-50',
							opt.enabled && selectedWorkflowType === opt.type && 'bg-accent',
							opt.enabled && selectedWorkflowType !== opt.type && 'hover:bg-accent/50',
						)}
						disabled={!opt.enabled}
						onclick={() => {
							if (opt.enabled) selectedWorkflowType = opt.type;
						}}
					>
						<Check
							class={cn(
								'size-3.5 shrink-0',
								selectedWorkflowType === opt.type ? 'opacity-100' : 'opacity-0',
							)}
						/>
						<div>
							<div class="font-medium">{opt.label}</div>
							<div class="text-muted-foreground text-xs">{opt.hint}</div>
						</div>
					</button>
				{/each}
			</div>

			<div class="space-y-1">
				<p class="text-muted-foreground text-xs font-medium">AI Model</p>
				<Select.Root type="single" bind:value={selectedModelId}>
					<Select.Trigger class="w-full">{selectedModelLabel}</Select.Trigger>
					<Select.Content>
						{#each models as model (model.id)}
							<Select.Item value={model.id}>{model.display_name}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>

			<Button class="w-full" size="sm" onclick={handleStart} disabled={!selectedModelId || loading}>
				{loading ? 'Starting...' : 'Start'}
			</Button>
		</div>
	</DropdownMenu.Content>
</DropdownMenu.Root>
