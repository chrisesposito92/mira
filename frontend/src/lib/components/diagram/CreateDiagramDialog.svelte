<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import type { DiagramCreate, Project } from '$lib/types';

	let {
		open = $bindable(false),
		projects = [],
		oncreate,
	}: {
		open: boolean;
		projects?: Project[];
		oncreate?: (data: DiagramCreate) => void | Promise<void>;
	} = $props();

	let customerName = $state('');
	let title = $state('');
	let projectId = $state('');
	let submitting = $state(false);

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!customerName.trim() || submitting) return;
		submitting = true;
		try {
			await oncreate?.({
				customer_name: customerName.trim(),
				title: title.trim() || undefined,
				project_id: projectId || undefined,
			});
		} finally {
			submitting = false;
		}
	}

	function reset() {
		customerName = '';
		title = '';
		projectId = '';
	}
</script>

<Dialog.Root
	bind:open
	onOpenChange={(v) => {
		if (!v) reset();
	}}
>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>New Diagram</Dialog.Title>
			<Dialog.Description>Create a new integration architecture diagram.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleSubmit} class="space-y-4">
			<div class="space-y-2">
				<Label for="diagram-customer-name">Customer Name *</Label>
				<Input
					id="diagram-customer-name"
					bind:value={customerName}
					placeholder="Acme Corp"
					required
				/>
			</div>
			<div class="space-y-2">
				<Label for="diagram-title">Title</Label>
				<Input
					id="diagram-title"
					bind:value={title}
					placeholder="e.g., Acme Corp Integration Architecture"
				/>
			</div>
			{#if projects.length > 0}
				<div class="space-y-2">
					<Label>Linked Project</Label>
					<Select.Root type="single" bind:value={projectId}>
						<Select.Trigger>
							{projects.find((p) => p.id === projectId)?.name || 'Select project...'}
						</Select.Trigger>
						<Select.Content>
							{#each projects as project}
								<Select.Item value={project.id}>{project.name}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>
			{/if}
			<Dialog.Footer>
				<Button variant="outline" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit" disabled={!customerName.trim() || submitting}>
					{submitting ? 'Creating...' : 'Create Diagram'}
				</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
