<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { Check, Loader2, Circle, AlertCircle } from 'lucide-svelte';
	import type { DocumentUploadProgress } from '$lib/types';
	import { DOC_PROCESSING_STAGES } from '$lib/types';

	let { progress }: { progress: DocumentUploadProgress } = $props();

	const currentStageIndex = $derived(
		progress.processingStage ? DOC_PROCESSING_STAGES.indexOf(progress.processingStage) : -1,
	);
</script>

{#if progress.phase === 'uploading'}
	<div class="bg-muted/50 rounded p-3">
		<div class="bg-muted h-2 overflow-hidden rounded-full">
			<div
				class="bg-primary h-full transition-all duration-300"
				style="width: {progress.uploadPercent}%"
			></div>
		</div>
		<p class="text-muted-foreground mt-1 text-xs">Uploading... {progress.uploadPercent}%</p>
	</div>
{:else if progress.phase === 'processing'}
	<div class="bg-muted/50 rounded p-3">
		<div class="flex gap-3">
			{#each DOC_PROCESSING_STAGES as stage, i}
				{@const completed = i < currentStageIndex}
				{@const current = i === currentStageIndex}
				<div class="flex flex-col items-center gap-1">
					{#if completed}
						<Check class="size-3.5 text-green-500" />
					{:else if current}
						<Loader2 class="text-primary size-3.5 animate-spin" />
					{:else}
						<Circle class="text-muted-foreground/50 size-3.5" />
					{/if}
					<span
						class={cn(
							'text-xs capitalize',
							completed && 'text-green-500',
							current && 'text-primary',
							!completed && !current && 'text-muted-foreground/50',
						)}
					>
						{stage}
					</span>
				</div>
			{/each}
		</div>
	</div>
{:else if progress.phase === 'complete'}
	<div class="flex items-center gap-1 text-xs text-green-600">
		<Check class="size-3.5" />
		<span>
			Processing complete{progress.chunkCount ? ` — ${progress.chunkCount} chunks` : ''}
		</span>
	</div>
{:else if progress.phase === 'error'}
	<div class="text-destructive flex items-center gap-1 text-xs">
		<AlertCircle class="size-3.5" />
		<span>{progress.error ?? 'Processing failed'}</span>
	</div>
{/if}
