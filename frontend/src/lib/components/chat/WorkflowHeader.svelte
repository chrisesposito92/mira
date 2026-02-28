<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { cn, snakeToTitle } from '$lib/utils.js';
	import type { WsConnectionState } from '$lib/types/workflow.js';
	import type { WorkflowStatus } from '$lib/types';

	let {
		currentStep = '',
		connectionState,
		status,
		modelName = '',
	}: {
		currentStep?: string;
		connectionState: WsConnectionState;
		status: WorkflowStatus | null;
		modelName?: string;
	} = $props();

	const connectionColor = $derived(
		connectionState === 'connected'
			? 'bg-green-500'
			: connectionState === 'connecting' || connectionState === 'reconnecting'
				? 'bg-yellow-500'
				: 'bg-red-500',
	);

	const stepLabel = $derived(currentStep ? snakeToTitle(currentStep) : '');

	const statusVariant = $derived<'default' | 'secondary' | 'destructive' | 'outline'>(
		status === 'completed'
			? 'default'
			: status === 'failed'
				? 'destructive'
				: status === 'running'
					? 'secondary'
					: 'outline',
	);
</script>

<div class="border-b px-4 py-3">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-3">
			<div class="flex items-center gap-2">
				<span class={cn('size-2 rounded-full', connectionColor)}></span>
				<span class="text-muted-foreground text-xs capitalize">{connectionState}</span>
			</div>
			{#if stepLabel}
				<span class="text-muted-foreground text-sm">{stepLabel}</span>
			{/if}
		</div>
		<div class="flex items-center gap-2">
			{#if modelName}
				<span class="text-muted-foreground text-xs">{modelName}</span>
			{/if}
			{#if status}
				<Badge variant={statusVariant}>{status}</Badge>
			{/if}
		</div>
	</div>
</div>
