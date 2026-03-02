<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { StatusBadge, UploadProgressBar } from '$lib/components/project';
	import { cn } from '$lib/utils.js';
	import { Upload, FileText, Trash2, Loader2 } from 'lucide-svelte';
	import type { Document, DocumentUploadProgress } from '$lib/types';

	let {
		documents = [],
		uploading = false,
		uploadProgress = null,
		onupload,
		ondelete,
	}: {
		documents?: Document[];
		uploading?: boolean;
		uploadProgress?: DocumentUploadProgress | null;
		onupload?: (file: File) => void;
		ondelete?: (id: string) => void;
	} = $props();

	const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'txt', 'csv'];
	const uploadBusy = $derived(
		uploading ||
			(uploadProgress != null &&
				uploadProgress.phase !== 'error' &&
				uploadProgress.phase !== 'complete'),
	);
	let dragOver = $state(false);
	let dropError = $state<string | null>(null);
	let fileInput = $state<HTMLInputElement | null>(null);

	function validateFile(file: File): boolean {
		const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
		if (!ALLOWED_EXTENSIONS.includes(ext)) {
			dropError = `File type '.${ext}' not supported. Use PDF, DOCX, TXT, or CSV.`;
			setTimeout(() => (dropError = null), 3000);
			return false;
		}
		return true;
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		const file = e.dataTransfer?.files[0];
		if (file && validateFile(file)) onupload?.(file);
	}

	function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file && validateFile(file)) onupload?.(file);
		input.value = '';
	}

	function formatSize(bytes: number | null): string {
		if (!bytes) return '';
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}
</script>

<div class="space-y-4">
	<!-- Drop zone -->
	<button
		type="button"
		class={cn(
			'border-muted-foreground/25 hover:border-primary/50 flex w-full flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-all duration-200',
			dragOver && 'border-primary bg-primary/10 scale-[1.01]',
			dropError && 'border-destructive bg-destructive/5',
			uploadBusy && 'pointer-events-none opacity-60',
		)}
		ondragover={(e) => {
			e.preventDefault();
			dragOver = true;
		}}
		ondragleave={() => (dragOver = false)}
		ondrop={handleDrop}
		onclick={() => fileInput?.click()}
		disabled={uploadBusy}
	>
		<Upload class="text-muted-foreground mb-2 size-8" />
		<p class="text-sm font-medium">
			{#if dropError}
				{dropError}
			{:else if uploadBusy}
				Processing...
			{:else if dragOver}
				Drop to upload
			{:else}
				Drop file here or click to browse
			{/if}
		</p>
		<p class="text-muted-foreground mt-1 text-xs">PDF, DOCX, TXT, CSV</p>
	</button>

	{#if uploadProgress}
		<UploadProgressBar progress={uploadProgress} />
	{/if}

	<input
		bind:this={fileInput}
		type="file"
		class="hidden"
		onchange={handleFileSelect}
		accept=".pdf,.docx,.txt,.csv"
	/>

	<!-- Document list -->
	{#if documents.length > 0}
		<div class="divide-y rounded-lg border">
			{#each documents as doc}
				<div class="flex items-center gap-3 p-3">
					<FileText class="text-muted-foreground size-4 shrink-0" />
					<div class="min-w-0 flex-1">
						<p class="truncate text-sm font-medium">{doc.filename}</p>
						<p class="text-muted-foreground text-xs">
							{doc.file_type}
							{#if doc.file_size_bytes}
								&middot; {formatSize(doc.file_size_bytes)}
							{/if}
							{#if doc.chunk_count > 0}
								&middot; {doc.chunk_count} chunks
							{/if}
						</p>
					</div>
					{#if doc.processing_status === 'processing'}
						<span class="text-muted-foreground flex items-center gap-1 text-xs">
							<Loader2 class="size-3 animate-spin" />
							Processing...
						</span>
					{:else}
						<StatusBadge status={doc.processing_status} />
					{/if}
					<Button variant="ghost" size="sm" onclick={() => ondelete?.(doc.id)}>
						<Trash2 class="size-3" />
					</Button>
				</div>
			{/each}
		</div>
	{/if}
</div>
