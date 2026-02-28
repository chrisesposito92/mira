<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Calendar, Building2 } from 'lucide-svelte';
	import type { Project } from '$lib/types';

	let { project, onclick }: { project: Project; onclick?: () => void } = $props();

	const formattedDate = $derived(
		new Date(project.updated_at).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
		}),
	);
</script>

<button class="w-full text-left" {onclick}>
	<Card.Root class="hover:border-primary/50 h-full transition-colors">
		<Card.Header>
			<Card.Title class="line-clamp-1">{project.name}</Card.Title>
			{#if project.customer_name}
				<Card.Description class="flex items-center gap-1">
					<Building2 class="size-3" />
					{project.customer_name}
				</Card.Description>
			{/if}
		</Card.Header>
		<Card.Content>
			{#if project.description}
				<p class="text-muted-foreground line-clamp-2 text-sm">{project.description}</p>
			{:else}
				<p class="text-muted-foreground/60 text-sm italic">No description</p>
			{/if}
		</Card.Content>
		<Card.Footer>
			<div class="text-muted-foreground flex items-center gap-1 text-xs">
				<Calendar class="size-3" />
				{formattedDate}
			</div>
		</Card.Footer>
	</Card.Root>
</button>
