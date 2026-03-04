<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Separator } from '$lib/components/ui/separator';
	import StatusBadge from '$lib/components/project/StatusBadge.svelte';
	import JsonEditor from './JsonEditor.svelte';
	import { snakeToTitle, formatDateTime } from '$lib/utils.js';
	import { Upload } from 'lucide-svelte';
	import type { GeneratedObject, GeneratedObjectUpdate } from '$lib/types';
	import { PUSHABLE_STATUSES } from '$lib/stores/objects.svelte.js';

	let {
		object = null,
		saving = false,
		pushing = false,
		onupdate,
		onpush,
	}: {
		object: GeneratedObject | null;
		saving?: boolean;
		pushing?: boolean;
		onupdate: (id: string, data: GeneratedObjectUpdate) => void;
		onpush?: (id: string) => void;
	} = $props();

	const isPushable = $derived(object !== null && PUSHABLE_STATUSES.has(object.status));

	let editedJson = $state('');
	let jsonValid = $state(true);
	let parsedData: Record<string, unknown> | null = $state(null);
	let lastObjectId = $state<string | null>(null);

	// Reset editor only when a different object is selected (not on same-object reference changes)
	$effect(() => {
		const id = object?.id ?? null;
		if (id !== lastObjectId) {
			lastObjectId = id;
			editedJson = object?.data ? JSON.stringify(object.data, null, 2) : '';
			parsedData = object?.data ?? null;
			jsonValid = true;
		}
	});

	function handleJsonChange(value: string) {
		editedJson = value;
		try {
			const parsed = JSON.parse(value);
			if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
				parsedData = null;
				jsonValid = false;
				return;
			}
			parsedData = parsed;
			jsonValid = true;
		} catch {
			parsedData = null;
			jsonValid = false;
		}
	}

	function handleSave() {
		if (!object || !jsonValid || !parsedData) return;
		onupdate(object.id, { data: parsedData });
	}

	function handleApprove() {
		if (!object) return;
		onupdate(object.id, { status: 'approved' });
	}

	function handleReject() {
		if (!object) return;
		onupdate(object.id, { status: 'rejected' });
	}
</script>

{#if object}
	<div class="flex h-full flex-col overflow-hidden">
		<!-- Header -->
		<div class="space-y-2 p-4">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-muted-foreground text-xs">{snakeToTitle(object.entity_type)}</p>
					<h2 class="text-lg font-semibold">
						{object.name || object.code || 'Untitled'}
					</h2>
					{#if object.code}
						<p class="text-muted-foreground font-mono text-sm">{object.code}</p>
					{/if}
				</div>
				<StatusBadge status={object.status} />
			</div>
			{#if object.m3ter_id}
				<div class="flex items-center gap-2">
					<Badge
						variant="outline"
						class="border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300"
					>
						m3ter ID: {object.m3ter_id}
					</Badge>
				</div>
			{/if}
			<div class="text-muted-foreground flex gap-4 text-xs">
				<span>Created: {formatDateTime(object.created_at)}</span>
				<span>Updated: {formatDateTime(object.updated_at)}</span>
			</div>
		</div>

		<Separator />

		<!-- JSON Editor -->
		<div class="flex-1 overflow-auto p-4">
			{#if object.data}
				<JsonEditor value={editedJson} onchange={handleJsonChange} />
			{:else}
				<p class="text-muted-foreground text-sm">No data available</p>
			{/if}

			<!-- Validation Errors -->
			{#if object.validation_errors && object.validation_errors.length > 0}
				<div class="mt-4 space-y-1">
					<p class="text-destructive text-sm font-medium">Validation Errors</p>
					{#each object.validation_errors as error}
						<div class="bg-destructive/10 rounded-md px-3 py-1.5 text-sm">
							<span class="font-medium">{error.field}:</span>
							{error.message}
							{#if error.severity !== 'error'}
								<span class="text-muted-foreground">({error.severity})</span>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<Separator />

		<!-- Actions -->
		<div class="flex items-center gap-2 p-4">
			<Button size="sm" disabled={!jsonValid || saving || !parsedData} onclick={handleSave}>
				{saving ? 'Saving...' : 'Save'}
			</Button>
			{#if object.status !== 'approved'}
				<Button size="sm" variant="outline" disabled={saving} onclick={handleApprove}>
					Approve
				</Button>
			{/if}
			{#if object.status !== 'rejected'}
				<Button size="sm" variant="outline" disabled={saving} onclick={handleReject}>Reject</Button>
			{/if}
			{#if isPushable}
				<Button
					size="sm"
					class="bg-green-600 text-white hover:bg-green-700"
					disabled={pushing || saving}
					onclick={() => object && onpush?.(object.id)}
				>
					<Upload class="mr-1 size-3.5" />
					{object.status === 'push_failed' ? 'Retry Push' : 'Push to m3ter'}
				</Button>
			{/if}
		</div>
	</div>
{:else}
	<div class="text-muted-foreground flex h-full items-center justify-center">
		<p>Select an object to view details</p>
	</div>
{/if}
