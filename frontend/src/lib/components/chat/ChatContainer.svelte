<script lang="ts">
	import ChatMessage from './ChatMessage.svelte';
	import ThinkingIndicator from './ThinkingIndicator.svelte';
	import type {
		ChatMessage as ChatMessageType,
		EntityDecision,
		ClarificationAnswer,
	} from '$lib/types/workflow.js';

	let {
		messages,
		thinking = false,
		currentStep = '',
		pendingDecisions = [],
		hasPendingEntities = false,
		ondecision,
		onclarify,
		onapproveall,
	}: {
		messages: ChatMessageType[];
		thinking?: boolean;
		currentStep?: string;
		pendingDecisions?: EntityDecision[];
		hasPendingEntities?: boolean;
		ondecision?: (decision: EntityDecision) => void;
		onclarify?: (answers: ClarificationAnswer[]) => void;
		onapproveall?: () => void;
	} = $props();

	let container: HTMLDivElement | undefined = $state();

	// Precompute last interactive indices once per render instead of O(n) scan per message
	const lastEntitiesIndex = $derived(messages.findLastIndex((m) => m.type === 'entities'));
	const lastClarificationIndex = $derived(
		messages.findLastIndex((m) => m.type === 'clarification'),
	);

	function isInteractive(msg: ChatMessageType, index: number): boolean {
		if (msg.type === 'entities') return index === lastEntitiesIndex && hasPendingEntities;
		if (msg.type === 'clarification') return index === lastClarificationIndex;
		return false;
	}

	const scrollTrigger = $derived(messages.length + (thinking ? 1 : 0));

	$effect(() => {
		// Auto-scroll when messages or thinking changes
		void scrollTrigger;
		if (container) {
			requestAnimationFrame(() => {
				container?.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
			});
		}
	});
</script>

<div bind:this={container} class="flex-1 overflow-y-auto">
	<div class="space-y-1 py-4">
		{#each messages as msg, i (msg.id)}
			<ChatMessage
				message={msg}
				interactive={isInteractive(msg, i)}
				decisions={msg.type === 'entities' ? pendingDecisions : []}
				{ondecision}
				{onclarify}
				{onapproveall}
			/>
		{/each}
		{#if thinking}
			<ThinkingIndicator step={currentStep} />
		{/if}
	</div>
</div>
