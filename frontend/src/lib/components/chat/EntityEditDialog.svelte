<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Label } from '$lib/components/ui/label';

	let {
		open = $bindable(false),
		entityName = '',
		config,
		onsave,
	}: {
		open: boolean;
		entityName?: string;
		config: Record<string, unknown>;
		onsave?: (edited: Record<string, unknown>) => void;
	} = $props();

	let jsonText = $state('');
	let parseError = $state<string | null>(null);

	$effect(() => {
		if (open) {
			jsonText = JSON.stringify(config, null, 2);
			parseError = null;
		}
	});

	function handleSave() {
		try {
			const parsed = JSON.parse(jsonText);
			parseError = null;
			onsave?.(parsed);
			open = false;
		} catch {
			parseError = 'Invalid JSON';
		}
	}
</script>

<Dialog.Root bind:open>
	<Dialog.Content class="sm:max-w-2xl">
		<Dialog.Header>
			<Dialog.Title>Edit {entityName || 'Entity'}</Dialog.Title>
			<Dialog.Description>Modify the JSON configuration and save your changes.</Dialog.Description>
		</Dialog.Header>
		<div class="space-y-2">
			<Label>Configuration</Label>
			<Textarea bind:value={jsonText} rows={16} class="font-mono text-sm" />
			{#if parseError}
				<p class="text-destructive text-sm">{parseError}</p>
			{/if}
		</div>
		<Dialog.Footer>
			<Button variant="outline" onclick={() => (open = false)}>Cancel</Button>
			<Button onclick={handleSave}>Save Changes</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
