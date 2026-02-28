<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { StatusBadge } from '$lib/components/project';
	import { TestTube, Pencil, Trash2 } from 'lucide-svelte';
	import type { OrgConnection } from '$lib/types';

	let {
		connection,
		testing = false,
		ontest,
		onedit,
		ondelete,
	}: {
		connection: OrgConnection;
		testing?: boolean;
		ontest?: () => void;
		onedit?: () => void;
		ondelete?: () => void;
	} = $props();

	const testedLabel = $derived(
		connection.last_tested_at
			? new Date(connection.last_tested_at).toLocaleDateString('en-US', {
					month: 'short',
					day: 'numeric',
					hour: 'numeric',
					minute: '2-digit',
				})
			: 'Never tested',
	);
</script>

<Card.Root>
	<Card.Header>
		<div class="flex items-start justify-between gap-2">
			<div>
				<Card.Title>{connection.org_name}</Card.Title>
				<Card.Description class="mt-1 font-mono text-xs">
					{connection.org_id}
				</Card.Description>
			</div>
			<StatusBadge status={connection.status} />
		</div>
	</Card.Header>
	<Card.Content>
		<div class="text-muted-foreground space-y-1 text-sm">
			<p>API: {connection.api_url}</p>
			<p>Last tested: {testedLabel}</p>
		</div>
	</Card.Content>
	<Card.Footer class="gap-2">
		<Button variant="outline" size="sm" onclick={ontest} disabled={testing}>
			<TestTube class="mr-1 size-3" />
			{testing ? 'Testing...' : 'Test'}
		</Button>
		<Button variant="outline" size="sm" onclick={onedit}>
			<Pencil class="mr-1 size-3" />
			Edit
		</Button>
		<Button variant="outline" size="sm" onclick={ondelete}>
			<Trash2 class="mr-1 size-3" />
			Delete
		</Button>
	</Card.Footer>
</Card.Root>
