<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { StatusBadge } from '$lib/components/project';
	import { DollarSign, ArrowRight } from 'lucide-svelte';
	import { cn, capitalize } from '$lib/utils.js';
	import type { UseCase } from '$lib/types';

	let {
		useCase,
		projectId,
	}: {
		useCase: UseCase;
		projectId?: string;
	} = $props();

	const billingLabel = $derived(
		useCase.billing_frequency ? capitalize(useCase.billing_frequency) : null,
	);

	const href = $derived(
		projectId ? `/projects/${projectId}/use-cases/${useCase.id}/control-panel` : undefined,
	);
</script>

<a {href} class={cn('block transition-shadow hover:shadow-md', href && 'cursor-pointer')}>
	<Card.Root>
		<Card.Header>
			<div class="flex items-start justify-between gap-2">
				<Card.Title class="line-clamp-1">{useCase.title}</Card.Title>
				<StatusBadge status={useCase.status} />
			</div>
			{#if useCase.description}
				<Card.Description class="line-clamp-2">{useCase.description}</Card.Description>
			{/if}
		</Card.Header>
		<Card.Content>
			<div class="text-muted-foreground flex flex-wrap gap-3 text-sm">
				{#if billingLabel}
					<span class="flex items-center gap-1">
						<DollarSign class="size-3" />
						{billingLabel} ({useCase.currency})
					</span>
				{/if}
				{#if useCase.target_billing_model}
					<span>{useCase.target_billing_model}</span>
				{/if}
				{#if href}
					<span class="flex items-center gap-1 text-xs">
						Open
						<ArrowRight class="size-3" />
					</span>
				{/if}
			</div>
		</Card.Content>
	</Card.Root>
</a>
