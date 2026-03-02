<script lang="ts">
	import * as Sheet from '$lib/components/ui/sheet';
	import { ChatContainer, WorkflowHeader } from '$lib/components/chat';
	import type {
		ChatMessage,
		EntityDecision,
		ClarificationAnswer,
		WsConnectionState,
		WorkflowStatus,
	} from '$lib/types';

	let {
		open = $bindable(false),
		messages,
		thinking,
		currentStep,
		connectionState,
		status,
		modelName,
		pendingDecisions,
		ondecision,
		onclarify,
	}: {
		open: boolean;
		messages: ChatMessage[];
		thinking: boolean;
		currentStep: string;
		connectionState: WsConnectionState;
		status: WorkflowStatus | null;
		modelName: string;
		pendingDecisions: EntityDecision[];
		ondecision: (decision: EntityDecision) => void;
		onclarify: (answers: ClarificationAnswer[]) => void;
	} = $props();
</script>

<Sheet.Root bind:open>
	<Sheet.Content side="right" class="flex w-full flex-col p-0 sm:max-w-lg">
		<Sheet.Header class="sr-only">
			<Sheet.Title>Workflow</Sheet.Title>
			<Sheet.Description>AI workflow chat panel</Sheet.Description>
		</Sheet.Header>
		<WorkflowHeader {currentStep} {connectionState} {status} {modelName} />
		<div class="flex-1 overflow-hidden">
			<ChatContainer
				{messages}
				{thinking}
				{currentStep}
				{pendingDecisions}
				{ondecision}
				{onclarify}
			/>
		</div>
	</Sheet.Content>
</Sheet.Root>
