<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Check, X, Loader2, Circle } from 'lucide-svelte';
	import { cn, snakeToTitle } from '$lib/utils.js';
	import type { PushSession } from '$lib/types';

	let {
		session,
		ondismiss,
	}: {
		session: PushSession;
		ondismiss: () => void;
	} = $props();

	const percentage = $derived(
		session.total > 0 ? Math.round((session.completed / session.total) * 100) : 0,
	);
</script>

<div class="bg-muted/30 border-b px-4 py-3">
	<!-- Progress bar -->
	<div class="mb-3 flex items-center gap-3">
		<div class="flex-1">
			<div class="mb-1 flex items-center justify-between text-sm">
				<span class="font-medium">
					{#if session.active}
						Pushing objects...
					{:else}
						Push complete
					{/if}
				</span>
				<span class="text-muted-foreground">
					{session.completed} / {session.total} ({percentage}%)
				</span>
			</div>
			<div class="bg-muted h-2 overflow-hidden rounded-full">
				<div
					class={cn(
						'h-full rounded-full transition-all duration-300',
						session.failed > 0 ? 'bg-yellow-500' : 'bg-green-500',
					)}
					style="width: {percentage}%"
				></div>
			</div>
		</div>
		{#if !session.active}
			<Button size="sm" variant="outline" onclick={ondismiss}>Dismiss</Button>
		{/if}
	</div>

	<!-- Summary when complete -->
	{#if !session.active}
		<p class="mb-2 text-sm">
			Pushed {session.succeeded} of {session.total} object{session.total !== 1 ? 's' : ''}
			{#if session.failed > 0}
				<span class="text-destructive">({session.failed} failed)</span>
			{/if}
		</p>
	{/if}

	<!-- Per-entity status list -->
	<div class="max-h-40 space-y-1 overflow-y-auto">
		{#each session.items as item (item.entityId)}
			<div class="flex items-center gap-2 text-sm">
				{#if item.status === 'pending'}
					<Circle class="text-muted-foreground size-4 shrink-0" />
				{:else if item.status === 'pushing'}
					<Loader2 class="size-4 shrink-0 animate-spin text-blue-500" />
				{:else if item.status === 'pushed'}
					<Check class="size-4 shrink-0 text-green-500" />
				{:else if item.status === 'push_failed'}
					<X class="size-4 shrink-0 text-red-500" />
				{/if}
				<span class="text-muted-foreground shrink-0">{snakeToTitle(item.entityType)}</span>
				<span class="flex-1 truncate">{item.entityId}</span>
				{#if item.error}
					<span class="text-destructive truncate text-xs">{item.error}</span>
				{/if}
			</div>
		{/each}
	</div>
</div>
