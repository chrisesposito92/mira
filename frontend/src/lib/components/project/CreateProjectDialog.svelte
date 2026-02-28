<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Textarea } from '$lib/components/ui/textarea';
	import type { ProjectCreate, OrgConnection } from '$lib/types';

	let {
		open = $bindable(false),
		connections = [],
		oncreate,
	}: {
		open: boolean;
		connections?: OrgConnection[];
		oncreate?: (data: ProjectCreate) => void | Promise<void>;
	} = $props();

	let name = $state('');
	let customerName = $state('');
	let description = $state('');
	let orgConnectionId = $state('');
	let submitting = $state(false);

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!name.trim() || submitting) return;
		submitting = true;
		try {
			await oncreate?.({
				name: name.trim(),
				customer_name: customerName.trim() || null,
				description: description.trim() || null,
				org_connection_id: orgConnectionId || null,
			});
			reset();
			open = false;
		} finally {
			submitting = false;
		}
	}

	function reset() {
		name = '';
		customerName = '';
		description = '';
		orgConnectionId = '';
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
			<Dialog.Title>New Project</Dialog.Title>
			<Dialog.Description>Create a new m3ter billing configuration project.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleSubmit} class="space-y-4">
			<div class="space-y-2">
				<Label for="project-name">Name *</Label>
				<Input id="project-name" bind:value={name} placeholder="My billing project" required />
			</div>
			<div class="space-y-2">
				<Label for="customer-name">Customer Name</Label>
				<Input id="customer-name" bind:value={customerName} placeholder="Acme Corp" />
			</div>
			<div class="space-y-2">
				<Label for="project-desc">Description</Label>
				<Textarea
					id="project-desc"
					bind:value={description}
					placeholder="Project description..."
					rows={3}
				/>
			</div>
			{#if connections.length > 0}
				<div class="space-y-2">
					<Label>Org Connection</Label>
					<Select.Root type="single" bind:value={orgConnectionId}>
						<Select.Trigger>
							{connections.find((c) => c.id === orgConnectionId)?.org_name ||
								'Select connection...'}
						</Select.Trigger>
						<Select.Content>
							{#each connections as conn}
								<Select.Item value={conn.id}>{conn.org_name}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>
			{/if}
			<Dialog.Footer>
				<Button variant="outline" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit" disabled={!name.trim() || submitting}>
					{submitting ? 'Creating...' : 'Create Project'}
				</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
