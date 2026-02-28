<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { StatusBadge } from '$lib/components/project';
	import { DollarSign } from 'lucide-svelte';
	import type { UseCase } from '$lib/types';

	let { useCase }: { useCase: UseCase } = $props();

	const billingLabel = $derived(
		useCase.billing_frequency
			? useCase.billing_frequency.charAt(0).toUpperCase() + useCase.billing_frequency.slice(1)
			: null,
	);
</script>

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
		</div>
	</Card.Content>
</Card.Root>
