<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { StatusBadge } from '$lib/components/project';
	import { Upload, FileText, Trash2 } from 'lucide-svelte';
	import type { Document } from '$lib/types';

	let {
		documents = [],
		uploading = false,
		onupload,
		ondelete,
	}: {
		documents?: Document[];
		uploading?: boolean;
		onupload?: (file: File) => void;
		ondelete?: (id: string) => void;
	} = $props();

	let dragOver = $state(false);
	let fileInput = $state<HTMLInputElement | null>(null);

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		const file = e.dataTransfer?.files[0];
		if (file) onupload?.(file);
	}

	function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) onupload?.(file);
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
		class="border-muted-foreground/25 hover:border-primary/50 flex w-full flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors {dragOver
			? 'border-primary bg-primary/5'
			: ''}"
		ondragover={(e) => {
			e.preventDefault();
			dragOver = true;
		}}
		ondragleave={() => (dragOver = false)}
		ondrop={handleDrop}
		onclick={() => fileInput?.click()}
		disabled={uploading}
	>
		<Upload class="text-muted-foreground mb-2 size-8" />
		<p class="text-sm font-medium">
			{uploading ? 'Uploading...' : 'Drop file here or click to browse'}
		</p>
		<p class="text-muted-foreground mt-1 text-xs">PDF, CSV, JSON, TXT, XLSX</p>
	</button>

	<input
		bind:this={fileInput}
		type="file"
		class="hidden"
		onchange={handleFileSelect}
		accept=".pdf,.csv,.json,.txt,.xlsx"
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
					<StatusBadge status={doc.processing_status} />
					<Button variant="ghost" size="sm" onclick={() => ondelete?.(doc.id)}>
						<Trash2 class="size-3" />
					</Button>
				</div>
			{/each}
		</div>
	{/if}
</div>
