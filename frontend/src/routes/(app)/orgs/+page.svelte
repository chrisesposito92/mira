<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import {
		OrgConnectionCard,
		CreateOrgConnectionDialog,
		EmptyState,
	} from '$lib/components/project';
	import { orgConnectionStore } from '$lib/stores';
	import { createApiClient, createOrgConnectionService } from '$lib/services';
	import { Plus, Building2 } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import type { OrgConnection, OrgConnectionCreate, OrgConnectionUpdate } from '$lib/types';

	let { data } = $props();

	let createOpen = $state(false);
	let editConnection = $state<OrgConnection | null>(null);
	let testingId = $state<string | null>(null);

	$effect(() => {
		orgConnectionStore.connections = data.connections;
	});

	function getService() {
		const client = createApiClient(data.supabase);
		return createOrgConnectionService(client);
	}

	async function handleCreate(formData: OrgConnectionCreate) {
		const service = getService();
		const conn = await orgConnectionStore.createConnection(service, formData);
		if (conn) toast.success('Connection added');
		else toast.error(orgConnectionStore.error ?? 'Failed to add connection');
	}

	async function handleUpdate(id: string, formData: OrgConnectionUpdate) {
		const service = getService();
		const conn = await orgConnectionStore.updateConnection(service, id, formData);
		if (conn) toast.success('Connection updated');
		else toast.error(orgConnectionStore.error ?? 'Failed to update');
	}

	async function handleDelete(id: string) {
		if (!confirm('Delete this org connection?')) return;
		const service = getService();
		const ok = await orgConnectionStore.deleteConnection(service, id);
		if (ok) toast.success('Connection deleted');
		else toast.error(orgConnectionStore.error ?? 'Failed to delete');
	}

	async function handleTest(id: string) {
		testingId = id;
		const service = getService();
		const result = await orgConnectionStore.testConnection(service, id);
		testingId = null;
		if (result?.success) toast.success(result.message);
		else toast.error(result?.message ?? orgConnectionStore.error ?? 'Test failed');
	}

	function handleEdit(conn: OrgConnection) {
		editConnection = conn;
		createOpen = true;
	}
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Org Connections</h1>
			<p class="text-muted-foreground mt-1">Manage your m3ter organization connections.</p>
		</div>
		<Button
			onclick={() => {
				editConnection = null;
				createOpen = true;
			}}
		>
			<Plus class="mr-2 size-4" />
			Add Connection
		</Button>
	</div>

	{#if orgConnectionStore.connections.length === 0}
		<EmptyState
			icon={Building2}
			title="No connections"
			description="Add an m3ter org connection to link your billing platform."
			actionLabel="Add Connection"
			onaction={() => {
				editConnection = null;
				createOpen = true;
			}}
		/>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each orgConnectionStore.connections as conn (conn.id)}
				<OrgConnectionCard
					connection={conn}
					testing={testingId === conn.id}
					ontest={() => handleTest(conn.id)}
					onedit={() => handleEdit(conn)}
					ondelete={() => handleDelete(conn.id)}
				/>
			{/each}
		</div>
	{/if}
</div>

<CreateOrgConnectionDialog
	bind:open={createOpen}
	{editConnection}
	oncreate={handleCreate}
	onupdate={handleUpdate}
/>
