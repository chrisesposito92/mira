<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Select from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Textarea } from '$lib/components/ui/textarea';
	import type { UseCaseCreate, BillingFrequency } from '$lib/types';

	let {
		open = $bindable(false),
		oncreate,
	}: {
		open: boolean;
		oncreate?: (data: UseCaseCreate) => void;
	} = $props();

	let title = $state('');
	let description = $state('');
	let billingFrequency = $state<string>('');
	let currency = $state('USD');
	let targetBillingModel = $state('');
	let contractStartDate = $state('');
	let notes = $state('');

	function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!title.trim()) return;
		oncreate?.({
			title: title.trim(),
			description: description.trim() || null,
			billing_frequency: (billingFrequency as BillingFrequency) || null,
			currency: currency || 'USD',
			target_billing_model: targetBillingModel.trim() || null,
			contract_start_date: contractStartDate || null,
			notes: notes.trim() || null,
		});
		reset();
		open = false;
	}

	function reset() {
		title = '';
		description = '';
		billingFrequency = '';
		currency = 'USD';
		targetBillingModel = '';
		contractStartDate = '';
		notes = '';
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
			<Dialog.Title>New Use Case</Dialog.Title>
			<Dialog.Description>Define a billing use case for this project.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleSubmit} class="space-y-4">
			<div class="space-y-2">
				<Label for="uc-title">Title *</Label>
				<Input id="uc-title" bind:value={title} placeholder="Usage-based API pricing" required />
			</div>
			<div class="space-y-2">
				<Label for="uc-desc">Description</Label>
				<Textarea
					id="uc-desc"
					bind:value={description}
					placeholder="Describe the billing use case..."
					rows={3}
				/>
			</div>
			<div class="grid grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label>Billing Frequency</Label>
					<Select.Root type="single" bind:value={billingFrequency}>
						<Select.Trigger>
							{billingFrequency
								? billingFrequency.charAt(0).toUpperCase() + billingFrequency.slice(1)
								: 'Select...'}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="monthly">Monthly</Select.Item>
							<Select.Item value="quarterly">Quarterly</Select.Item>
							<Select.Item value="annually">Annually</Select.Item>
						</Select.Content>
					</Select.Root>
				</div>
				<div class="space-y-2">
					<Label for="uc-currency">Currency</Label>
					<Input id="uc-currency" bind:value={currency} placeholder="USD" />
				</div>
			</div>
			<div class="space-y-2">
				<Label for="uc-model">Target Billing Model</Label>
				<Input id="uc-model" bind:value={targetBillingModel} placeholder="e.g. per_unit, tiered" />
			</div>
			<div class="space-y-2">
				<Label for="uc-date">Contract Start Date</Label>
				<Input id="uc-date" type="date" bind:value={contractStartDate} />
			</div>
			<div class="space-y-2">
				<Label for="uc-notes">Notes</Label>
				<Textarea id="uc-notes" bind:value={notes} placeholder="Additional notes..." rows={2} />
			</div>
			<Dialog.Footer>
				<Button variant="outline" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit" disabled={!title.trim()}>Create Use Case</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
