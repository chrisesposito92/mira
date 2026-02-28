<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import EntityEditDialog from './EntityEditDialog.svelte';
	import { Check, Pencil, X, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-svelte';
	import { cn } from '$lib/utils.js';
	import type { EntityError, EntityDecision } from '$lib/types/workflow.js';

	let {
		entityIndex,
		entityName,
		config,
		errors = [],
		interactive = false,
		existingDecision,
		ondecision,
	}: {
		entityIndex: number;
		entityName: string;
		config: Record<string, unknown>;
		errors?: EntityError[];
		interactive?: boolean;
		existingDecision?: EntityDecision;
		ondecision?: (decision: EntityDecision) => void;
	} = $props();

	let expanded = $state(false);
	let editOpen = $state(false);

	const warningCount = $derived(errors.filter((e) => e.severity === 'warning').length);
	const errorCount = $derived(errors.filter((e) => e.severity === 'error').length);

	function approve() {
		ondecision?.({ index: entityIndex, action: 'approve' });
	}

	function reject() {
		ondecision?.({ index: entityIndex, action: 'reject' });
	}

	function handleEditSave(edited: Record<string, unknown>) {
		ondecision?.({ index: entityIndex, action: 'edit', data: edited });
	}
</script>

<Card.Root class="overflow-hidden">
	<Card.Header class="pb-2">
		<div class="flex items-start justify-between gap-2">
			<div class="flex items-center gap-2">
				<Card.Title class="text-sm font-medium">{entityName}</Card.Title>
				{#if existingDecision}
					<Badge
						variant={existingDecision.action === 'approve'
							? 'default'
							: existingDecision.action === 'edit'
								? 'secondary'
								: 'destructive'}
					>
						{existingDecision.action === 'approve'
							? 'approved'
							: existingDecision.action === 'edit'
								? 'edited'
								: 'rejected'}
					</Badge>
				{/if}
			</div>
			<button
				class="text-muted-foreground hover:text-foreground transition-colors"
				onclick={() => (expanded = !expanded)}
			>
				{#if expanded}
					<ChevronUp class="size-4" />
				{:else}
					<ChevronDown class="size-4" />
				{/if}
			</button>
		</div>
		{#if errorCount > 0 || warningCount > 0}
			<div class="flex gap-2 text-xs">
				{#if errorCount > 0}
					<span class="text-destructive flex items-center gap-1">
						<AlertTriangle class="size-3" />
						{errorCount} error{errorCount > 1 ? 's' : ''}
					</span>
				{/if}
				{#if warningCount > 0}
					<span class="flex items-center gap-1 text-yellow-600">
						<AlertTriangle class="size-3" />
						{warningCount} warning{warningCount > 1 ? 's' : ''}
					</span>
				{/if}
			</div>
		{/if}
	</Card.Header>

	{#if expanded}
		<Card.Content class="pt-0">
			<pre class="bg-muted max-h-64 overflow-auto rounded-md p-3 text-xs">{JSON.stringify(
					config,
					null,
					2,
				)}</pre>
			{#if errors.length > 0}
				<div class="mt-2 space-y-1">
					{#each errors as err}
						<p
							class={cn(
								'text-xs',
								err.severity === 'error' ? 'text-destructive' : 'text-yellow-600',
							)}
						>
							<span class="font-medium">{err.field}:</span>
							{err.message}
						</p>
					{/each}
				</div>
			{/if}
		</Card.Content>
	{/if}

	{#if interactive && !existingDecision}
		<div class="flex gap-2 border-t px-4 py-2">
			<Button size="sm" variant="default" onclick={approve}>
				<Check class="mr-1 size-3" />
				Approve
			</Button>
			<Button size="sm" variant="outline" onclick={() => (editOpen = true)}>
				<Pencil class="mr-1 size-3" />
				Edit
			</Button>
			<Button size="sm" variant="destructive" onclick={reject}>
				<X class="mr-1 size-3" />
				Reject
			</Button>
		</div>
	{/if}
</Card.Root>

<EntityEditDialog bind:open={editOpen} {entityName} {config} onsave={handleEditSave} />
