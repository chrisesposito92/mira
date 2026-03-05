<script lang="ts">
	import * as Collapsible from '$lib/components/ui/collapsible';
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Textarea } from '$lib/components/ui/textarea';
	import { ChevronRight, ChevronDown, Pencil } from 'lucide-svelte';
	import { capitalize, formatDate } from '$lib/utils.js';
	import type { UseCase, UseCaseUpdate, BillingFrequency } from '$lib/types';

	let {
		useCase,
		objectCount,
		saving,
		workflowActive = false,
		onupdate,
		onreset,
	}: {
		useCase: UseCase;
		objectCount: number;
		saving: boolean;
		workflowActive?: boolean;
		onupdate: (data: UseCaseUpdate) => Promise<UseCase | null>;
		onreset: () => Promise<void>;
	} = $props();

	let open = $state(true);
	let editing = $state(false);
	let showResetDialog = $state(false);
	let pendingUpdate = $state<UseCaseUpdate | null>(null);

	// Edit form state
	let title = $state('');
	let description = $state('');
	let billingFrequency = $state<BillingFrequency | ''>('');
	let currency = $state('');
	let targetBillingModel = $state('');
	let contractStartDate = $state('');
	let notes = $state('');

	function startEditing() {
		title = useCase.title;
		description = useCase.description ?? '';
		billingFrequency = useCase.billing_frequency ?? '';
		currency = useCase.currency ?? 'USD';
		targetBillingModel = useCase.target_billing_model ?? '';
		contractStartDate = useCase.contract_start_date ?? '';
		notes = useCase.notes ?? '';
		editing = true;
	}

	function cancelEditing() {
		editing = false;
	}

	function buildUpdateData(): UseCaseUpdate {
		return {
			title: title.trim() || null,
			description: description.trim() || null,
			billing_frequency: billingFrequency || null,
			currency: currency || 'USD',
			target_billing_model: targetBillingModel.trim() || null,
			contract_start_date: contractStartDate || null,
			notes: notes.trim() || null,
		};
	}

	async function handleSave() {
		const data = buildUpdateData();
		if (objectCount > 0 && !workflowActive) {
			pendingUpdate = data;
			showResetDialog = true;
		} else {
			const result = await onupdate(data);
			if (result) editing = false;
		}
	}

	async function confirmSave(andReset: boolean) {
		showResetDialog = false;
		if (pendingUpdate) {
			const result = await onupdate(pendingUpdate);
			if (result) {
				if (andReset) await onreset();
				editing = false;
			}
		}
		pendingUpdate = null;
	}

	function displayDate(dateStr: string | null): string {
		if (!dateStr) return '-';
		try {
			return formatDate(dateStr);
		} catch {
			return dateStr;
		}
	}

	function displayField(str: string | null): string {
		if (!str) return '-';
		return capitalize(str);
	}
</script>

<Collapsible.Root bind:open>
	<Collapsible.Trigger
		class="hover:bg-muted flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium"
	>
		{#if open}
			<ChevronDown class="size-4" />
		{:else}
			<ChevronRight class="size-4" />
		{/if}
		Use Case Details
	</Collapsible.Trigger>

	<Collapsible.Content class="px-2 pt-1 pb-3">
		{#if editing}
			<!-- Edit mode -->
			<div class="space-y-3">
				<div class="space-y-1">
					<Label for="meta-title" class="text-xs">Title *</Label>
					<Input id="meta-title" bind:value={title} class="h-8 text-sm" required />
				</div>
				<div class="space-y-1">
					<Label for="meta-desc" class="text-xs">Description</Label>
					<Textarea
						id="meta-desc"
						bind:value={description}
						rows={2}
						class="text-sm"
						placeholder="Describe the billing use case..."
					/>
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div class="space-y-1">
						<Label class="text-xs">Billing Frequency</Label>
						<Select.Root type="single" bind:value={billingFrequency}>
							<Select.Trigger class="h-8 text-sm">
								{billingFrequency ? displayField(billingFrequency) : 'Select...'}
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="monthly">Monthly</Select.Item>
								<Select.Item value="quarterly">Quarterly</Select.Item>
								<Select.Item value="annually">Annually</Select.Item>
							</Select.Content>
						</Select.Root>
					</div>
					<div class="space-y-1">
						<Label for="meta-currency" class="text-xs">Currency</Label>
						<Input id="meta-currency" bind:value={currency} class="h-8 text-sm" placeholder="USD" />
					</div>
				</div>
				<div class="space-y-1">
					<Label for="meta-model" class="text-xs">Target Billing Model</Label>
					<Input
						id="meta-model"
						bind:value={targetBillingModel}
						class="h-8 text-sm"
						placeholder="e.g. per_unit, tiered"
					/>
				</div>
				<div class="space-y-1">
					<Label for="meta-date" class="text-xs">Contract Start Date</Label>
					<Input id="meta-date" type="date" bind:value={contractStartDate} class="h-8 text-sm" />
				</div>
				<div class="space-y-1">
					<Label for="meta-notes" class="text-xs">Notes</Label>
					<Textarea
						id="meta-notes"
						bind:value={notes}
						rows={2}
						class="text-sm"
						placeholder="Additional notes..."
					/>
				</div>
				<div class="flex justify-end gap-2">
					<Button variant="outline" size="sm" onclick={cancelEditing} disabled={saving}>
						Cancel
					</Button>
					<Button size="sm" onclick={handleSave} disabled={!title.trim() || saving}>
						{saving ? 'Saving...' : 'Save'}
					</Button>
				</div>
			</div>
		{:else}
			<!-- View mode -->
			<div class="space-y-2">
				<div class="flex items-start justify-between gap-2">
					<p class="text-sm font-semibold">{useCase.title}</p>
					<Button variant="ghost" size="sm" class="size-7 shrink-0 p-0" onclick={startEditing}>
						<Pencil class="size-3.5" />
					</Button>
				</div>
				{#if useCase.description}
					<p class="text-muted-foreground line-clamp-2 text-xs">{useCase.description}</p>
				{/if}
				<div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
					<div>
						<span class="text-muted-foreground">Frequency</span>
						<p>{displayField(useCase.billing_frequency)}</p>
					</div>
					<div>
						<span class="text-muted-foreground">Currency</span>
						<p>{useCase.currency ?? '-'}</p>
					</div>
					<div>
						<span class="text-muted-foreground">Model</span>
						<p>{useCase.target_billing_model ?? '-'}</p>
					</div>
					<div>
						<span class="text-muted-foreground">Start Date</span>
						<p>{displayDate(useCase.contract_start_date)}</p>
					</div>
				</div>
				{#if useCase.notes}
					<p class="text-muted-foreground text-xs italic">{useCase.notes}</p>
				{/if}
			</div>
		{/if}
	</Collapsible.Content>
</Collapsible.Root>

<AlertDialog.Root bind:open={showResetDialog}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Reset generated objects?</AlertDialog.Title>
			<AlertDialog.Description>
				This use case has {objectCount} generated object{objectCount !== 1 ? 's' : ''}. Changing the
				use case details may make them outdated. Would you like to reset them?
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel onclick={() => (showResetDialog = false)}>Cancel</AlertDialog.Cancel>
			<Button variant="outline" onclick={() => confirmSave(false)}>Save Without Reset</Button>
			<Button onclick={() => confirmSave(true)}>Save & Reset</Button>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
