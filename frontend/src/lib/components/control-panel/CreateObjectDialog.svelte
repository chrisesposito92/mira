<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { JsonEditor } from '$lib/components/control-panel';
	import { ENTITY_TYPE_ORDER } from '$lib/stores/objects.svelte.js';
	import { snakeToTitle } from '$lib/utils.js';
	import type { CreateObjectPayload, EntityType } from '$lib/types';

	let {
		open = $bindable(false),
		oncreate,
		templates = {},
	}: {
		open: boolean;
		oncreate?: (data: CreateObjectPayload) => void | Promise<void>;
		templates?: Record<string, Record<string, unknown>>;
	} = $props();

	let entityType = $state<string>('');
	let prevEntityType = '';
	let name = $state('');
	let code = $state('');
	let jsonContent = $state('{}');
	let submitting = $state(false);

	// Update JSON editor only when entity type actually changes (not on late template loads)
	$effect(() => {
		if (entityType !== prevEntityType) {
			prevEntityType = entityType;
			if (entityType && templates[entityType]) {
				jsonContent = JSON.stringify({ ...templates[entityType] }, null, 2);
			} else if (entityType) {
				jsonContent = '{}';
			}
		}
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!entityType || submitting) return;
		submitting = true;
		try {
			let data: Record<string, unknown> = {};
			try {
				data = JSON.parse(jsonContent);
			} catch {
				// If JSON is invalid, use empty object
				data = {};
			}
			// Merge name/code from form fields into data
			if (name.trim()) data.name = name.trim();
			if (code.trim()) data.code = code.trim();

			await oncreate?.({
				entity_type: entityType as EntityType,
				name: name.trim() || undefined,
				code: code.trim() || undefined,
				data,
			});
			reset();
			open = false;
		} finally {
			submitting = false;
		}
	}

	function reset() {
		entityType = '';
		prevEntityType = '';
		name = '';
		code = '';
		jsonContent = '{}';
	}
</script>

<Dialog.Root
	bind:open
	onOpenChange={(v) => {
		if (!v) reset();
	}}
>
	<Dialog.Content class="sm:max-w-2xl">
		<Dialog.Header>
			<Dialog.Title>New Object</Dialog.Title>
			<Dialog.Description>Create a new m3ter billing object manually.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleSubmit} class="space-y-4">
			<div class="space-y-2">
				<Label>Entity Type *</Label>
				<Select.Root type="single" bind:value={entityType}>
					<Select.Trigger>
						{entityType ? snakeToTitle(entityType) : 'Select entity type...'}
					</Select.Trigger>
					<Select.Content>
						{#each ENTITY_TYPE_ORDER as et}
							<Select.Item value={et}>{snakeToTitle(et)}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>
			<div class="grid grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label for="obj-name">Name</Label>
					<Input id="obj-name" bind:value={name} placeholder="Object name" />
				</div>
				<div class="space-y-2">
					<Label for="obj-code">Code</Label>
					<Input id="obj-code" bind:value={code} placeholder="object_code" />
				</div>
			</div>
			<div class="space-y-2">
				<Label>Data (JSON)</Label>
				<div class="h-64">
					<JsonEditor value={jsonContent} onchange={(v) => (jsonContent = v)} />
				</div>
			</div>
			<Dialog.Footer>
				<Button variant="outline" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit" disabled={!entityType || submitting}>
					{submitting ? 'Creating...' : 'Create Object'}
				</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
