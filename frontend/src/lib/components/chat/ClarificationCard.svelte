<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Label } from '$lib/components/ui/label';
	import { cn } from '$lib/utils.js';
	import type { ClarificationQuestion, ClarificationAnswer } from '$lib/types/workflow.js';

	let {
		questions,
		interactive = false,
		onsubmit,
	}: {
		questions: ClarificationQuestion[];
		interactive?: boolean;
		onsubmit?: (answers: ClarificationAnswer[]) => void;
	} = $props();

	// Track selections by question index: selected_option is the numeric index into options[]
	let answers = $state<Record<number, { selected_option?: number; free_text?: string }>>({});

	$effect(() => {
		const initial: Record<number, { selected_option?: number; free_text?: string }> = {};
		for (let i = 0; i < questions.length; i++) {
			initial[i] = { selected_option: undefined, free_text: undefined };
		}
		answers = initial;
	});

	function handleSubmit() {
		const result: ClarificationAnswer[] = questions.map((_, i) => ({
			selected_option: answers[i]?.selected_option,
			free_text: answers[i]?.free_text?.trim() || undefined,
		}));
		onsubmit?.(result);
	}

	const allAnswered = $derived(
		questions.every((_, i) => {
			const a = answers[i];
			return a?.selected_option !== undefined || a?.free_text?.trim();
		}),
	);
</script>

<Card.Root>
	<Card.Header>
		<Card.Title class="text-sm">Clarification Needed</Card.Title>
	</Card.Header>
	<Card.Content class="space-y-6">
		{#each questions as q, qi}
			<div class="space-y-2">
				<p class="text-sm font-medium">{q.question}</p>
				{#if q.recommendation}
					<p class="text-muted-foreground text-xs">Recommended: {q.recommendation}</p>
				{/if}
				<div class="space-y-1">
					{#each q.options as opt, oi}
						<label
							class={cn(
								'flex cursor-pointer items-start gap-2 rounded-md border p-2 transition-colors',
								interactive ? 'hover:bg-muted' : '',
								answers[qi]?.selected_option === oi ? 'border-primary bg-primary/5' : '',
							)}
						>
							<input
								type="radio"
								name="q-{qi}"
								value={oi}
								disabled={!interactive}
								checked={answers[qi]?.selected_option === oi}
								onchange={() => {
									if (answers[qi]) answers[qi].selected_option = oi;
								}}
								class="mt-0.5"
							/>
							<div>
								<span class="text-sm">{opt.label}</span>
								{#if opt.description}
									<p class="text-muted-foreground text-xs">{opt.description}</p>
								{/if}
							</div>
						</label>
					{/each}
				</div>
				{#if q.allows_free_text && interactive}
					<div class="space-y-1">
						<Label class="text-xs">Or provide your own answer</Label>
						<Textarea
							rows={2}
							placeholder="Type your answer..."
							value={answers[qi]?.free_text ?? ''}
							oninput={(e) => {
								if (answers[qi]) answers[qi].free_text = e.currentTarget.value;
							}}
						/>
					</div>
				{/if}
			</div>
		{/each}
		{#if interactive}
			<Button onclick={handleSubmit} disabled={!allAnswered} class="w-full">Submit Answers</Button>
		{/if}
	</Card.Content>
</Card.Root>
