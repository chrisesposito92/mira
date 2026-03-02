<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Textarea } from '$lib/components/ui/textarea';
	import UseCaseResultCard from './UseCaseResultCard.svelte';
	import { GeneratorWebSocketClient } from '$lib/services/generator-websocket.js';
	import { createApiClient, createUseCaseService } from '$lib/services';
	import { SvelteSet } from 'svelte/reactivity';
	import { cn } from '$lib/utils.js';
	import { Loader2, Upload, FileText, X, AlertCircle } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import type { SupabaseClient } from '@supabase/supabase-js';
	import type {
		GeneratedUseCase,
		GeneratorWsMessage,
		GeneratorClarificationQuestion,
	} from '$lib/types/generator.js';
	import type { ClarificationAnswer, LlmModel } from '$lib/types';

	type DialogStep = 'input' | 'progress' | 'clarification' | 'results';

	let {
		open = $bindable(false),
		customerName,
		projectId,
		token,
		models,
		supabase,
		onSaved,
	}: {
		open: boolean;
		customerName: string;
		projectId: string;
		token: string;
		models: LlmModel[];
		supabase: SupabaseClient;
		onSaved?: () => void;
	} = $props();

	// --- State ---
	let step = $state<DialogStep>('input');
	let numUseCases = $state('2');
	let notes = $state('');
	let modelId = $state('');
	let attachmentText = $state<string | null>(null);
	let attachmentFile = $state<File | null>(null);
	let extracting = $state(false);
	let statusMessages = $state<string[]>([]);
	let clarificationQuestions = $state<GeneratorClarificationQuestion[]>([]);
	let generatedUseCases = $state<GeneratedUseCase[]>([]);
	let selectedIndices = new SvelteSet<number>();
	let errorMessage = $state<string | null>(null);
	let saving = $state(false);
	let wsClient: GeneratorWebSocketClient | null = null;

	// Clarification answers state
	let answers = $state<Record<number, { selected_option?: number; free_text?: string }>>({});

	const allAnswered = $derived(
		clarificationQuestions.every((_, i) => {
			const a = answers[i];
			return a?.selected_option !== undefined || a?.free_text?.trim();
		}),
	);

	const canGenerate = $derived(customerName && modelId);
	const selectedCount = $derived(selectedIndices.size);

	// Set default model on mount
	$effect(() => {
		if (models.length > 0 && !modelId) {
			modelId = models[0].id;
		}
	});

	// --- File extraction ---
	async function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		await extractFile(file);
	}

	async function handleFileDrop(e: DragEvent) {
		e.preventDefault();
		const file = e.dataTransfer?.files[0];
		if (!file) return;
		await extractFile(file);
	}

	async function extractFile(file: File) {
		const allowed = [
			'application/pdf',
			'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
			'text/plain',
		];
		if (!allowed.includes(file.type) && !file.name.match(/\.(pdf|docx|txt)$/i)) {
			toast.error('Only PDF, DOCX, and TXT files are accepted');
			return;
		}

		extracting = true;
		attachmentFile = file;
		try {
			const client = createApiClient(supabase, token);
			const formData = new FormData();
			formData.append('file', file);
			const result = await client.upload<{ text: string }>(
				`/api/projects/${projectId}/generate-use-cases/extract-text`,
				formData,
			);
			attachmentText = result.text;
		} catch {
			toast.error('Failed to extract text from file');
			attachmentFile = null;
			attachmentText = null;
		} finally {
			extracting = false;
		}
	}

	function removeAttachment() {
		attachmentFile = null;
		attachmentText = null;
	}

	// --- WebSocket ---
	function handleWsMessage(msg: GeneratorWsMessage) {
		switch (msg.type) {
			case 'gen_status':
				statusMessages = [...statusMessages, msg.message];
				break;
			case 'gen_clarification': {
				clarificationQuestions = msg.questions;
				// Initialize answers
				const initial: Record<number, { selected_option?: number; free_text?: string }> = {};
				for (let i = 0; i < msg.questions.length; i++) {
					initial[i] = { selected_option: undefined, free_text: undefined };
				}
				answers = initial;
				step = 'clarification';
				break;
			}
			case 'gen_use_cases':
				generatedUseCases = msg.use_cases;
				// Select all by default
				selectedIndices.clear();
				msg.use_cases.forEach((_, i) => selectedIndices.add(i));
				step = 'results';
				break;
			case 'gen_error':
				errorMessage = msg.message;
				break;
		}
	}

	function handleWsClose() {
		// Only show error if we're still in progress and haven't received results
		if (step === 'progress' && !errorMessage) {
			errorMessage = 'Connection lost. Please try again.';
		}
	}

	function startGeneration() {
		errorMessage = null;
		statusMessages = [];
		step = 'progress';

		wsClient = new GeneratorWebSocketClient(handleWsMessage, handleWsClose);
		wsClient.connect(projectId, token, () => {
			wsClient?.send({
				type: 'start_generate',
				customer_name: customerName,
				num_use_cases: parseInt(numUseCases),
				notes: notes.trim() || undefined,
				attachment_text: attachmentText || undefined,
				model_id: modelId,
			});
		});
	}

	// --- Clarification ---
	function submitClarification() {
		const result: ClarificationAnswer[] = clarificationQuestions.map((_, i) => ({
			selected_option: answers[i]?.selected_option,
			free_text: answers[i]?.free_text?.trim() || undefined,
		}));
		wsClient?.send({ type: 'clarify', answers: result });
		statusMessages = [...statusMessages, 'Clarification submitted, continuing...'];
		step = 'progress';
	}

	// --- Save ---
	async function saveSelected() {
		saving = true;
		try {
			const client = createApiClient(supabase, token);
			const useCaseService = createUseCaseService(client);
			const indices = [...selectedIndices];

			const results = await Promise.allSettled(
				indices.map((idx) => {
					const uc = generatedUseCases[idx];
					return useCaseService.create(projectId, {
						title: uc.title,
						description: uc.description || null,
						billing_frequency: uc.billing_frequency,
						currency: uc.currency || 'USD',
						target_billing_model: uc.target_billing_model,
						notes: uc.notes,
					});
				}),
			);

			let successCount = 0;
			results.forEach((r, i) => {
				if (r.status === 'fulfilled') {
					successCount++;
				} else {
					toast.error(`Failed to save: ${generatedUseCases[indices[i]].title}`);
				}
			});

			if (successCount > 0) {
				toast.success(`Saved ${successCount} use case${successCount > 1 ? 's' : ''}`);
				onSaved?.();
				open = false;
			}
		} finally {
			saving = false;
		}
	}

	// --- Toggle selection ---
	function toggleSelection(index: number) {
		if (selectedIndices.has(index)) {
			selectedIndices.delete(index);
		} else {
			selectedIndices.add(index);
		}
	}

	// --- Reset & cleanup ---
	function reset() {
		step = 'input';
		notes = '';
		attachmentText = null;
		attachmentFile = null;
		extracting = false;
		statusMessages = [];
		clarificationQuestions = [];
		generatedUseCases = [];
		selectedIndices.clear();
		errorMessage = null;
		saving = false;
		answers = {};
		wsClient?.disconnect();
		wsClient = null;
	}

	function retry() {
		wsClient?.disconnect();
		wsClient = null;
		errorMessage = null;
		statusMessages = [];
		step = 'input';
	}
</script>

<Dialog.Root
	bind:open
	onOpenChange={(v) => {
		if (!v) reset();
	}}
>
	<Dialog.Content class="sm:max-w-2xl">
		<Dialog.Header>
			<Dialog.Title>
				{#if step === 'input'}
					Generate Use Cases
				{:else if step === 'progress'}
					Generating...
				{:else if step === 'clarification'}
					Clarification Needed
				{:else}
					Generated Use Cases
				{/if}
			</Dialog.Title>
			<Dialog.Description>
				{#if step === 'input'}
					AI will generate billing use cases based on your customer context.
				{:else if step === 'progress'}
					Please wait while use cases are being generated.
				{:else if step === 'clarification'}
					Answer the following questions to help refine the generation.
				{:else}
					Select the use cases you want to save to this project.
				{/if}
			</Dialog.Description>
		</Dialog.Header>

		<!-- Step 1: Input Form -->
		{#if step === 'input'}
			<div class="space-y-4">
				<div class="space-y-2">
					<Label for="gen-customer">Customer Name</Label>
					<Input id="gen-customer" value={customerName} readonly class="bg-muted" />
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div class="space-y-2">
						<Label>Number of Use Cases</Label>
						<Select.Root type="single" bind:value={numUseCases}>
							<Select.Trigger>
								{numUseCases}
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="1">1</Select.Item>
								<Select.Item value="2">2</Select.Item>
								<Select.Item value="3">3</Select.Item>
							</Select.Content>
						</Select.Root>
					</div>
					<div class="space-y-2">
						<Label>Model</Label>
						<Select.Root type="single" bind:value={modelId}>
							<Select.Trigger>
								{models.find((m) => m.id === modelId)?.display_name ?? 'Select model...'}
							</Select.Trigger>
							<Select.Content>
								{#each models as model}
									<Select.Item value={model.id}>{model.display_name}</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>
				</div>

				<div class="space-y-2">
					<Label for="gen-notes">Notes (optional)</Label>
					<Textarea
						id="gen-notes"
						bind:value={notes}
						placeholder="Any context about the customer's billing needs..."
						rows={3}
					/>
				</div>

				<div class="space-y-2">
					<Label>Attachment (optional)</Label>
					{#if attachmentFile}
						<div class="bg-muted flex items-center gap-2 rounded-md border p-3">
							<FileText class="text-muted-foreground size-4 shrink-0" />
							<span class="flex-1 truncate text-sm">{attachmentFile.name}</span>
							{#if extracting}
								<Loader2 class="text-muted-foreground size-4 animate-spin" />
								<span class="text-muted-foreground text-xs">Extracting...</span>
							{:else if attachmentText}
								<span class="text-muted-foreground text-xs">
									{attachmentText.length} chars
								</span>
							{/if}
							<button
								type="button"
								class="text-muted-foreground hover:text-foreground"
								onclick={removeAttachment}
								disabled={extracting}
							>
								<X class="size-4" />
							</button>
						</div>
					{:else}
						<div
							class="hover:bg-muted/50 flex cursor-pointer flex-col items-center gap-2 rounded-md border border-dashed p-6 transition-colors"
							role="button"
							tabindex="0"
							ondragover={(e) => e.preventDefault()}
							ondrop={handleFileDrop}
							onclick={() => document.getElementById('gen-file-input')?.click()}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									document.getElementById('gen-file-input')?.click();
								}
							}}
						>
							<Upload class="text-muted-foreground size-6" />
							<span class="text-muted-foreground text-sm">
								Drop a file here or click to browse
							</span>
							<span class="text-muted-foreground text-xs">PDF, DOCX, TXT</span>
						</div>
						<input
							id="gen-file-input"
							type="file"
							accept=".pdf,.docx,.txt"
							class="hidden"
							onchange={handleFileSelect}
						/>
					{/if}
				</div>

				<Dialog.Footer>
					<Button variant="outline" type="button" onclick={() => (open = false)}>Cancel</Button>
					<Button disabled={!canGenerate || extracting} onclick={startGeneration}>Generate</Button>
				</Dialog.Footer>
			</div>

			<!-- Step 2: Progress -->
		{:else if step === 'progress'}
			<div class="space-y-4 py-4">
				{#if errorMessage}
					<div
						class="bg-destructive/10 text-destructive flex items-start gap-2 rounded-md border p-3"
					>
						<AlertCircle class="mt-0.5 size-4 shrink-0" />
						<div class="space-y-1">
							<p class="text-sm font-medium">Error</p>
							<p class="text-sm">{errorMessage}</p>
						</div>
					</div>
					<Dialog.Footer>
						<Button variant="outline" onclick={() => (open = false)}>Close</Button>
						<Button onclick={retry}>Try Again</Button>
					</Dialog.Footer>
				{:else}
					<div class="flex flex-col items-center gap-4">
						<Loader2 class="text-primary size-8 animate-spin" />
						<div class="w-full space-y-1">
							{#each statusMessages as msg}
								<p class="text-muted-foreground text-center text-sm">{msg}</p>
							{/each}
						</div>
					</div>
				{/if}
			</div>

			<!-- Step 3: Clarification -->
		{:else if step === 'clarification'}
			<div class="max-h-[60vh] space-y-6 overflow-y-auto py-2">
				{#each clarificationQuestions as q, qi}
					<div class="space-y-2">
						<p class="text-sm font-medium">{q.question}</p>
						{#if q.recommendation}
							<p class="text-muted-foreground text-xs">
								Recommended: {q.recommendation}
							</p>
						{/if}
						<div class="space-y-1">
							{#each q.options as opt, oi}
								<label
									class={cn(
										'hover:bg-muted flex cursor-pointer items-start gap-2 rounded-md border p-2 transition-colors',
										answers[qi]?.selected_option === oi ? 'border-primary bg-primary/5' : '',
									)}
								>
									<input
										type="radio"
										name="gen-q-{qi}"
										value={oi}
										checked={answers[qi]?.selected_option === oi}
										onchange={() => {
											if (answers[qi]) answers[qi].selected_option = oi;
										}}
										class="mt-0.5"
									/>
									<div>
										<span class="text-sm">{opt.label}</span>
										{#if opt.description}
											<p class="text-muted-foreground text-xs">
												{opt.description}
											</p>
										{/if}
									</div>
								</label>
							{/each}
						</div>
					</div>
				{/each}
			</div>
			<Dialog.Footer>
				<Button disabled={!allAnswered} onclick={submitClarification}>Submit Answers</Button>
			</Dialog.Footer>

			<!-- Step 4: Results -->
		{:else if step === 'results'}
			<div class="max-h-[60vh] space-y-3 overflow-y-auto py-2">
				{#each generatedUseCases as uc, i}
					<UseCaseResultCard
						useCase={uc}
						selected={selectedIndices.has(i)}
						onToggle={() => toggleSelection(i)}
					/>
				{/each}
			</div>
			<Dialog.Footer>
				<Button variant="outline" onclick={() => (open = false)}>Cancel</Button>
				<Button disabled={selectedCount === 0 || saving} onclick={saveSelected}>
					{#if saving}
						<Loader2 class="mr-1 size-4 animate-spin" />
						Saving...
					{:else}
						Save Selected ({selectedCount})
					{/if}
				</Button>
			</Dialog.Footer>
		{/if}
	</Dialog.Content>
</Dialog.Root>
