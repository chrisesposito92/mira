<script lang="ts">
	import * as Sheet from '$lib/components/ui/sheet';
	import { ChatContainer, WorkflowHeader } from '$lib/components/chat';
	import { Loader2 } from 'lucide-svelte';
	import type {
		ChatMessage,
		EntityDecision,
		ClarificationAnswer,
		WsConnectionState,
		WorkflowStatus,
	} from '$lib/types';

	let {
		open = $bindable(false),
		loading = false,
		messages,
		thinking,
		currentStep,
		connectionState,
		status,
		modelName,
		pendingDecisions,
		hasPendingEntities = false,
		ondecision,
		onclarify,
		onapproveall,
	}: {
		open: boolean;
		loading: boolean;
		messages: ChatMessage[];
		thinking: boolean;
		currentStep: string;
		connectionState: WsConnectionState;
		status: WorkflowStatus | null;
		modelName: string;
		pendingDecisions: EntityDecision[];
		hasPendingEntities?: boolean;
		ondecision: (decision: EntityDecision) => void;
		onclarify: (answers: ClarificationAnswer[]) => void;
		onapproveall?: () => void;
	} = $props();
</script>

<Sheet.Root bind:open>
	<Sheet.Content side="right" class="flex w-full flex-col p-0 sm:max-w-lg">
		<Sheet.Header class="sr-only">
			<Sheet.Title>Workflow</Sheet.Title>
			<Sheet.Description>AI workflow chat panel</Sheet.Description>
		</Sheet.Header>
		<WorkflowHeader {currentStep} {connectionState} {status} {modelName} />
		<div class="flex min-h-0 flex-1 flex-col overflow-hidden">
			{#if loading && messages.length === 0}
				<div class="flex h-full flex-col items-center justify-center gap-3">
					<Loader2 class="text-muted-foreground size-6 animate-spin" />
					<p class="text-muted-foreground text-sm">Starting workflow...</p>
				</div>
			{:else}
				<ChatContainer
					{messages}
					{thinking}
					{currentStep}
					{pendingDecisions}
					{hasPendingEntities}
					{ondecision}
					{onclarify}
					{onapproveall}
				/>
			{/if}
		</div>
	</Sheet.Content>
</Sheet.Root>
