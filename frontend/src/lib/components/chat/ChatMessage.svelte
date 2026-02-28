<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import EntityCard from './EntityCard.svelte';
	import ClarificationCard from './ClarificationCard.svelte';
	import { CheckCircle, AlertCircle, Activity, MessageSquare, ThumbsUp } from 'lucide-svelte';
	import type { ChatMessage, EntityDecision, ClarificationAnswer } from '$lib/types/workflow.js';

	let {
		message,
		interactive = false,
		decisions = [],
		ondecision,
		onclarify,
	}: {
		message: ChatMessage;
		interactive?: boolean;
		decisions?: EntityDecision[];
		ondecision?: (decision: EntityDecision) => void;
		onclarify?: (answers: ClarificationAnswer[]) => void;
	} = $props();
</script>

{#if message.type === 'status'}
	<div class="flex items-center gap-2 px-4 py-2">
		<Activity class="text-muted-foreground size-4" />
		<span class="text-muted-foreground text-sm">{message.message}</span>
	</div>
{:else if message.type === 'entities'}
	<div class="space-y-2 px-4 py-2">
		<div class="flex items-center gap-2">
			<MessageSquare class="text-muted-foreground size-4" />
			<span class="text-sm font-medium capitalize">
				{message.entity_type} Review
			</span>
			<Badge variant="outline">{message.entities.length} entities</Badge>
		</div>
		<div class="space-y-2">
			{#each message.entities as entity, i}
				<EntityCard
					entityIndex={i}
					entityName={(entity['name'] as string) ?? `Entity ${i + 1}`}
					config={entity}
					errors={message.errors.filter((e) => e.field.startsWith(`[${i}]`))}
					{interactive}
					existingDecision={decisions.find((d) => d.index === i)}
					{ondecision}
				/>
			{/each}
		</div>
	</div>
{:else if message.type === 'clarification'}
	<div class="px-4 py-2">
		<ClarificationCard questions={message.questions} {interactive} onsubmit={onclarify} />
	</div>
{:else if message.type === 'user_decision'}
	<div class="flex items-center gap-2 px-4 py-2">
		<ThumbsUp class="size-4 text-blue-500" />
		<span class="text-sm">
			Submitted {message.decisions.length} decision{message.decisions.length > 1 ? 's' : ''}
		</span>
	</div>
{:else if message.type === 'user_clarification'}
	<div class="flex items-center gap-2 px-4 py-2">
		<MessageSquare class="size-4 text-blue-500" />
		<span class="text-sm">
			Answered {message.answers.length} question{message.answers.length > 1 ? 's' : ''}
		</span>
	</div>
{:else if message.type === 'complete'}
	<div class="mx-4 my-2 flex items-center gap-2 rounded-lg bg-green-50 p-3 dark:bg-green-950/20">
		<CheckCircle class="size-5 text-green-600" />
		<span class="text-sm font-medium text-green-800 dark:text-green-300">{message.message}</span>
	</div>
{:else if message.type === 'error'}
	<div class="bg-destructive/10 mx-4 my-2 flex items-center gap-2 rounded-lg p-3">
		<AlertCircle class="text-destructive size-5" />
		<span class="text-destructive text-sm font-medium">{message.message}</span>
	</div>
{/if}
