<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import StatusBadge from '$lib/components/project/StatusBadge.svelte';
	import JsonEditor from './JsonEditor.svelte';
	import { snakeToTitle } from '$lib/utils.js';
	import type { GeneratedObject, GeneratedObjectUpdate } from '$lib/types';

	let {
		object = null,
		saving = false,
		onupdate,
	}: {
		object: GeneratedObject | null;
		saving?: boolean;
		onupdate: (id: string, data: GeneratedObjectUpdate) => void;
	} = $props();

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

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleString();
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
				<p class="text-muted-foreground text-xs">m3ter ID: {object.m3ter_id}</p>
			{/if}
			<div class="text-muted-foreground flex gap-4 text-xs">
				<span>Created: {formatDate(object.created_at)}</span>
				<span>Updated: {formatDate(object.updated_at)}</span>
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
		</div>
	</div>
{:else}
	<div class="text-muted-foreground flex h-full items-center justify-center">
		<p>Select an object to view details</p>
	</div>
{/if}
