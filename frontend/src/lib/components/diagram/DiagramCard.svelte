<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Building2, FolderKanban, Trash2, Network } from 'lucide-svelte';
	import { formatRelativeTime } from '$lib/utils.js';
	import type { DiagramListItem } from '$lib/types';

	let {
		diagram,
		ondelete,
	}: {
		diagram: DiagramListItem;
		ondelete?: (id: string) => void;
	} = $props();

	const displayName = $derived(diagram.customer_name || diagram.title || 'Untitled');

	const relativeTime = $derived(formatRelativeTime(diagram.updated_at));
</script>

<a href="/diagrams/{diagram.id}" class="block" data-sveltekit-preload-data="hover">
	<Card.Root class="hover:border-primary/50 h-full overflow-hidden transition-colors">
		<div class="bg-muted relative aspect-video w-full overflow-hidden rounded-t-xl">
			{#if diagram.thumbnail_base64}
				<img src={diagram.thumbnail_base64} alt="" class="h-full w-full object-cover" />
			{:else}
				<div class="flex h-full w-full items-center justify-center">
					<Network class="text-muted-foreground size-8" aria-hidden="true" />
				</div>
			{/if}
		</div>
		<Card.Header>
			<Card.Title class="line-clamp-1">{displayName}</Card.Title>
			{#if diagram.customer_name && diagram.title}
				<Card.Description class="flex items-center gap-1">
					<Building2 class="size-3" />
					{diagram.customer_name}
				</Card.Description>
			{/if}
		</Card.Header>
		<Card.Content>
			{#if diagram.project_id}
				<p class="text-muted-foreground flex items-center gap-1 text-sm">
					<FolderKanban class="size-3" />
					Linked to project
				</p>
			{/if}
		</Card.Content>
		<Card.Footer>
			<div class="flex w-full items-center justify-between">
				<span class="text-muted-foreground text-xs">{relativeTime}</span>
				{#if ondelete}
					<Button
						variant="ghost"
						size="icon"
						class="text-muted-foreground hover:text-destructive h-8 w-8"
						aria-label="Delete diagram {displayName}"
						onclick={(e) => {
							e.stopPropagation();
							ondelete(diagram.id);
						}}
					>
						<Trash2 class="size-4" />
					</Button>
				{/if}
			</div>
		</Card.Footer>
	</Card.Root>
</a>
