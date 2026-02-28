<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import type { OrgConnectionCreate, OrgConnectionUpdate, OrgConnection } from '$lib/types';

	let {
		open = $bindable(false),
		editConnection = null,
		oncreate,
		onupdate,
	}: {
		open: boolean;
		editConnection?: OrgConnection | null;
		oncreate?: (data: OrgConnectionCreate) => void;
		onupdate?: (id: string, data: OrgConnectionUpdate) => void;
	} = $props();

	let orgName = $state('');
	let orgId = $state('');
	let apiUrl = $state('https://api.m3ter.com');
	let clientId = $state('');
	let clientSecret = $state('');

	const isEdit = $derived(!!editConnection);

	$effect(() => {
		if (editConnection) {
			orgName = editConnection.org_name;
			orgId = editConnection.org_id;
			apiUrl = editConnection.api_url;
			clientId = '';
			clientSecret = '';
		}
	});

	function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (isEdit && editConnection) {
			onupdate?.(editConnection.id, {
				org_name: orgName.trim() || null,
				api_url: apiUrl.trim() || null,
				client_id: clientId.trim() || null,
				client_secret: clientSecret.trim() || null,
			});
		} else {
			if (!orgName.trim() || !orgId.trim() || !clientId.trim() || !clientSecret.trim()) return;
			oncreate?.({
				org_name: orgName.trim(),
				org_id: orgId.trim(),
				api_url: apiUrl.trim() || 'https://api.m3ter.com',
				client_id: clientId.trim(),
				client_secret: clientSecret.trim(),
			});
		}
		reset();
		open = false;
	}

	function reset() {
		orgName = '';
		orgId = '';
		apiUrl = 'https://api.m3ter.com';
		clientId = '';
		clientSecret = '';
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
			<Dialog.Title>{isEdit ? 'Edit Connection' : 'Add Org Connection'}</Dialog.Title>
			<Dialog.Description>
				{isEdit
					? 'Update your m3ter organization connection.'
					: 'Connect to an m3ter organization.'}
			</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleSubmit} class="space-y-4">
			<div class="space-y-2">
				<Label for="org-name">Organization Name *</Label>
				<Input id="org-name" bind:value={orgName} placeholder="My m3ter Org" required />
			</div>
			{#if !isEdit}
				<div class="space-y-2">
					<Label for="org-id">Organization ID *</Label>
					<Input id="org-id" bind:value={orgId} placeholder="org-uuid" required />
				</div>
			{/if}
			<div class="space-y-2">
				<Label for="api-url">API URL</Label>
				<Input id="api-url" bind:value={apiUrl} placeholder="https://api.m3ter.com" />
			</div>
			<div class="space-y-2">
				<Label for="client-id">{isEdit ? 'Client ID (leave blank to keep)' : 'Client ID *'}</Label>
				<Input id="client-id" bind:value={clientId} placeholder="Client ID" required={!isEdit} />
			</div>
			<div class="space-y-2">
				<Label for="client-secret"
					>{isEdit ? 'Client Secret (leave blank to keep)' : 'Client Secret *'}</Label
				>
				<Input
					id="client-secret"
					type="password"
					bind:value={clientSecret}
					placeholder="Client Secret"
					required={!isEdit}
				/>
			</div>
			<Dialog.Footer>
				<Button variant="outline" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit">{isEdit ? 'Update' : 'Add Connection'}</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
