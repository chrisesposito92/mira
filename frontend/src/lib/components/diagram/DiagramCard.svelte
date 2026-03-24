<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Calendar, Building2, FolderKanban, Trash2 } from 'lucide-svelte';
	import type { DiagramListItem } from '$lib/types';

	let {
		diagram,
		ondelete,
	}: {
		diagram: DiagramListItem;
		ondelete?: (id: string) => void;
	} = $props();

	const displayName = $derived(diagram.customer_name || diagram.title || 'Untitled');

	const formattedDate = $derived(
		new Date(diagram.updated_at).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
		}),
	);
</script>

<Card.Root class="hover:border-primary/50 h-full transition-colors">
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
			<div class="text-muted-foreground flex items-center gap-1 text-xs">
				<Calendar class="size-3" />
				{formattedDate}
			</div>
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
