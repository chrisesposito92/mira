<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { cn, capitalize } from '$lib/utils.js';
	import { Check } from 'lucide-svelte';
	import type { GeneratedUseCase } from '$lib/types/generator.js';

	let {
		useCase,
		selected,
		onToggle,
	}: {
		useCase: GeneratedUseCase;
		selected: boolean;
		onToggle: () => void;
	} = $props();

	let expanded = $state(false);

	const billingLabel = $derived(
		useCase.billing_frequency ? capitalize(useCase.billing_frequency) : null,
	);
</script>

<div
	class="w-full cursor-pointer text-left"
	role="button"
	tabindex="0"
	onclick={onToggle}
	onkeydown={(e) => {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			onToggle();
		}
	}}
>
	<Card.Root class={cn('transition-all', selected ? 'ring-primary ring-2' : 'hover:shadow-md')}>
		<Card.Header>
			<div class="flex items-start justify-between gap-2">
				<Card.Title class="line-clamp-1 text-sm">{useCase.title}</Card.Title>
				<div
					class={cn(
						'flex size-5 shrink-0 items-center justify-center rounded border transition-colors',
						selected
							? 'bg-primary border-primary text-primary-foreground'
							: 'border-muted-foreground/30',
					)}
				>
					{#if selected}
						<Check class="size-3" />
					{/if}
				</div>
			</div>
			{#if useCase.description}
				<Card.Description
					class={cn(!expanded && 'line-clamp-3', 'cursor-text break-words')}
					onclick={(e: MouseEvent) => {
						e.stopPropagation();
						expanded = !expanded;
					}}
				>
					{useCase.description}
				</Card.Description>
				{#if useCase.description.length > 200}
					<button
						type="button"
						class="text-muted-foreground hover:text-foreground text-xs underline"
						onclick={(e: MouseEvent) => {
							e.stopPropagation();
							expanded = !expanded;
						}}
					>
						{expanded ? 'Show less' : 'Show more'}
					</button>
				{/if}
			{/if}
		</Card.Header>
		<Card.Content>
			<div class="flex flex-wrap gap-2">
				{#if billingLabel}
					<Badge variant="secondary">{billingLabel}</Badge>
				{/if}
				{#if useCase.currency}
					<Badge variant="outline">{useCase.currency}</Badge>
				{/if}
				{#if useCase.target_billing_model}
					<Badge variant="outline">{useCase.target_billing_model}</Badge>
				{/if}
			</div>
		</Card.Content>
	</Card.Root>
</div>
