<script lang="ts">
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import { Button } from '$lib/components/ui/button';

	let {
		open = $bindable(false),
		diagramName = '',
		onconfirm,
	}: {
		open: boolean;
		diagramName: string;
		onconfirm?: () => void | Promise<void>;
	} = $props();

	let deleting = $state(false);

	async function handleConfirm() {
		deleting = true;
		try {
			await onconfirm?.();
			open = false;
		} finally {
			deleting = false;
		}
	}
</script>

<AlertDialog.Root bind:open>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete diagram?</AlertDialog.Title>
			<AlertDialog.Description>
				This will permanently delete the diagram "{diagramName}". This action cannot be
				undone.
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
			<Button variant="destructive" onclick={handleConfirm} disabled={deleting}>
				{deleting ? 'Deleting...' : 'Delete Diagram'}
			</Button>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
