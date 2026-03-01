<script lang="ts">
	import { onDestroy } from 'svelte';
	import { ChatContainer, WorkflowHeader, WorkflowLauncher } from '$lib/components/chat';
	import { workflowStore } from '$lib/stores';
	import { createApiClient, createWorkflowService } from '$lib/services';
	import { toast } from 'svelte-sonner';
	import { ArrowLeft } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import type { EntityDecision, ClarificationAnswer, WorkflowType } from '$lib/types/workflow.js';

	let { data } = $props();
	let restored = false;

	function getService() {
		const client = createApiClient(data.supabase);
		return createWorkflowService(client);
	}

	// Initialize store with page data
	$effect(() => {
		workflowStore.models = data.models;
		workflowStore.workflows = data.workflows;

		// Restore interrupted workflow once (skip on subsequent $effect re-runs from session refresh)
		if (!restored && data.interruptedWorkflow && data.session?.access_token) {
			restored = true;
			workflowStore.restoreFromInterrupt(
				data.interruptedWorkflow,
				data.session.access_token,
				data.interruptedMessages,
			);
		}
	});

	// Refresh workflows list when returning to the launcher after a workflow completes,
	// so the WF2 gate picks up the newly-completed WF1 without a full page reload.
	let prevShowLauncher = $state(false);
	$effect(() => {
		if (showLauncher && !prevShowLauncher && workflowStore.isCompleted) {
			const service = getService();
			workflowStore.loadWorkflows(service, data.useCase.id);
		}
		prevShowLauncher = showLauncher;
	});

	onDestroy(() => {
		workflowStore.clear();
	});

	async function handleStart(modelId: string, workflowType: WorkflowType) {
		if (!data.session?.access_token) {
			toast.error('Not authenticated');
			return;
		}
		const service = getService();
		const wf = await workflowStore.startWorkflow(
			service,
			data.useCase.id,
			modelId,
			data.session.access_token,
			workflowType,
		);
		if (!wf) {
			toast.error(workflowStore.error ?? 'Failed to start workflow');
		}
	}

	function handleDecision(decision: EntityDecision) {
		workflowStore.submitDecision(decision);
	}

	function handleClarification(answers: ClarificationAnswer[]) {
		workflowStore.submitClarificationAnswers(answers);
	}

	const showLauncher = $derived(
		(!workflowStore.workflow && !workflowStore.loading) ||
			(workflowStore.isCompleted && !workflowStore.loading),
	);
	const showChat = $derived(workflowStore.workflow !== null);

	const modelName = $derived(
		workflowStore.models.find((m) => m.id === workflowStore.workflow?.model_id)?.display_name ?? '',
	);
</script>

<div class="flex h-full flex-col">
	<!-- Top bar -->
	<div class="flex items-center gap-3 border-b px-4 py-3">
		<Button variant="ghost" size="sm" href="/projects/{data.project?.id ?? ''}">
			<ArrowLeft class="mr-1 size-4" />
			Back
		</Button>
		<div class="flex-1">
			<h1 class="text-sm font-semibold">{data.useCase.title}</h1>
			{#if data.project}
				<p class="text-muted-foreground text-xs">{data.project.name}</p>
			{/if}
		</div>
	</div>

	{#if showChat}
		<WorkflowHeader
			currentStep={workflowStore.currentStep}
			connectionState={workflowStore.connectionState}
			status={workflowStore.workflow?.status ?? null}
			{modelName}
		/>
		<ChatContainer
			messages={workflowStore.messages}
			thinking={workflowStore.thinking}
			currentStep={workflowStore.currentStep}
			pendingDecisions={workflowStore.pendingDecisions}
			ondecision={handleDecision}
			onclarify={handleClarification}
		/>
	{/if}

	{#if showLauncher}
		<div class="flex-1">
			<WorkflowLauncher
				models={workflowStore.models}
				workflows={workflowStore.workflows}
				loading={workflowStore.loading}
				onstart={handleStart}
			/>
		</div>
	{/if}

	{#if workflowStore.error}
		<div class="bg-destructive/10 text-destructive border-t px-4 py-2 text-sm">
			{workflowStore.error}
		</div>
	{/if}
</div>
