import type { WorkflowService } from '$lib/services/workflow.js';
import { WebSocketClient } from '$lib/services/websocket.js';
import type {
	Workflow,
	LlmModel,
	ChatMessage,
	WsServerMessage,
	WsConnectionState,
	EntityDecision,
	ClarificationQuestion,
	ClarificationAnswer,
	ChatMessageResponse,
	WorkflowType,
	EntityType,
} from '$lib/types';

class WorkflowStore {
	messages = $state<ChatMessage[]>([]);
	workflow = $state<Workflow | null>(null);
	workflows = $state<Workflow[]>([]);
	models = $state<LlmModel[]>([]);
	connectionState = $state<WsConnectionState>('disconnected');
	thinking = $state(false);
	currentStep = $state('');
	loading = $state(false);
	error = $state<string | null>(null);
	pendingEntities = $state<{
		entity_type: EntityType;
		entities: Array<Record<string, unknown>>;
	} | null>(null);
	pendingClarification = $state<ClarificationQuestion[] | null>(null);
	pendingDecisions = $state<EntityDecision[]>([]);

	// Derived
	isConnected = $derived(this.connectionState === 'connected');
	isInterrupted = $derived(this.workflow?.status === 'interrupted');
	isRunning = $derived(this.workflow?.status === 'running');
	isCompleted = $derived(this.workflow?.status === 'completed');
	isFailed = $derived(this.workflow?.status === 'failed');
	hasPendingInteraction = $derived(
		this.pendingEntities !== null || this.pendingClarification !== null,
	);

	private ws: WebSocketClient | null = null;
	private messageCounter = 0;
	private restoredFromHistory = false;

	private nextId(): string {
		return `msg-${Date.now()}-${++this.messageCounter}`;
	}

	async loadModels(service: WorkflowService) {
		try {
			this.models = await service.listModels();
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load models';
		}
	}

	async loadWorkflows(service: WorkflowService, useCaseId: string) {
		try {
			this.workflows = await service.list(useCaseId);
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load workflows';
		}
	}

	async startWorkflow(
		service: WorkflowService,
		useCaseId: string,
		modelId: string,
		token: string,
		workflowType?: WorkflowType,
	) {
		this.loading = true;
		this.error = null;
		this.messages = [];
		this.pendingEntities = null;
		this.pendingClarification = null;
		this.pendingDecisions = [];
		try {
			this.workflow = await service.start(useCaseId, modelId, workflowType);
			this.connectWebSocket(this.workflow.id, token);
			return this.workflow;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to start workflow';
			return null;
		} finally {
			this.loading = false;
		}
	}

	private connectWebSocket(workflowId: string, token: string) {
		this.disconnectWebSocket();
		this.ws = new WebSocketClient(
			(msg) => this.handleWsMessage(msg),
			(state) => {
				this.connectionState = state;
			},
		);
		this.ws.connect(workflowId, token);
	}

	private disconnectWebSocket() {
		if (this.ws) {
			this.ws.disconnect();
			this.ws = null;
		}
	}

	handleWsMessage(msg: WsServerMessage) {
		const now = new Date().toISOString();

		switch (msg.type) {
			case 'status':
				this.thinking = true;
				this.currentStep = msg.step;
				this.messages = [
					...this.messages,
					{
						id: this.nextId(),
						type: 'status',
						step: msg.step,
						message: msg.message,
						timestamp: now,
					},
				];
				break;

			case 'entities':
				this.thinking = false;
				this.pendingEntities = {
					entity_type: msg.entity_type,
					entities: msg.entities,
				};
				this.pendingDecisions = [];
				// Skip appending if this is a replay of already-restored history
				if (this.restoredFromHistory) {
					this.restoredFromHistory = false;
					break;
				}
				this.messages = [
					...this.messages,
					{
						id: this.nextId(),
						type: 'entities',
						entity_type: msg.entity_type,
						entities: msg.entities,
						errors: msg.errors,
						timestamp: now,
					},
				];
				break;

			case 'clarification':
				this.thinking = false;
				this.pendingClarification = msg.questions;
				// Skip appending if this is a replay of already-restored history
				if (this.restoredFromHistory) {
					this.restoredFromHistory = false;
					break;
				}
				this.messages = [
					...this.messages,
					{
						id: this.nextId(),
						type: 'clarification',
						questions: msg.questions,
						timestamp: now,
					},
				];
				break;

			case 'complete':
				this.thinking = false;
				this.currentStep = '';
				this.pendingEntities = null;
				this.pendingClarification = null;
				if (this.workflow) {
					this.workflow = { ...this.workflow, status: 'completed' };
				}
				this.messages = [
					...this.messages,
					{
						id: this.nextId(),
						type: 'complete',
						message: msg.message,
						timestamp: now,
					},
				];
				break;

			case 'error':
				this.thinking = false;
				if (this.workflow) {
					this.workflow = { ...this.workflow, status: 'failed' };
				}
				this.messages = [
					...this.messages,
					{
						id: this.nextId(),
						type: 'error',
						message: msg.message,
						timestamp: now,
					},
				];
				break;
		}
	}

	approveAll() {
		if (!this.pendingEntities) return;
		for (let i = 0; i < this.pendingEntities.entities.length; i++) {
			const existing = this.pendingDecisions.find((d) => d.index === i);
			if (!existing) {
				this.pendingDecisions = [...this.pendingDecisions, { index: i, action: 'approve' }];
			}
		}
		this.submitAllDecisions();
	}

	submitDecision(decision: EntityDecision) {
		const existing = this.pendingDecisions.find((d) => d.index === decision.index);
		if (existing) {
			// Allow replacing an edit with approve/reject, but ignore true duplicates
			if (existing.action !== 'edit') return;
			this.pendingDecisions = this.pendingDecisions.map((d) =>
				d.index === decision.index ? decision : d,
			);
		} else {
			this.pendingDecisions = [...this.pendingDecisions, decision];
		}

		// If all entities have decisions, send the resume
		if (
			this.pendingEntities &&
			this.pendingDecisions.length >= this.pendingEntities.entities.length
		) {
			this.submitAllDecisions();
		}
	}

	private submitAllDecisions() {
		if (!this.ws || this.pendingDecisions.length === 0 || !this.pendingEntities) return;

		const decisions = [...this.pendingDecisions];
		this.ws.send({ type: 'resume', decisions });

		this.messages = [
			...this.messages,
			{
				id: this.nextId(),
				type: 'user_decision',
				decisions,
				timestamp: new Date().toISOString(),
			},
		];

		this.thinking = true;
		this.pendingEntities = null;
		this.pendingDecisions = [];
	}

	submitClarificationAnswers(answers: ClarificationAnswer[]) {
		if (!this.ws || !this.pendingClarification) return;

		this.ws.send({ type: 'clarify', answers });

		this.messages = [
			...this.messages,
			{
				id: this.nextId(),
				type: 'user_clarification',
				answers,
				timestamp: new Date().toISOString(),
			},
		];

		this.thinking = true;
		this.pendingClarification = null;
	}

	async restoreFromInterrupt(
		workflow: Workflow,
		token: string,
		persistedMessages?: ChatMessageResponse[],
	) {
		this.workflow = workflow;
		if (persistedMessages && persistedMessages.length > 0) {
			this.messages = persistedMessages.map((m) => this.persistedToChatMessage(m));
			// Flag that history was loaded — the next entities/clarification WS message
			// is a replay of the current interrupt and should not be appended again
			this.restoredFromHistory = true;
		}
		this.connectWebSocket(workflow.id, token);
	}

	async loadMessages(service: WorkflowService, workflowId: string) {
		try {
			const persisted = await service.listMessages(workflowId);
			this.messages = persisted.map((m) => this.persistedToChatMessage(m));
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load messages';
		}
	}

	private persistedToChatMessage(m: ChatMessageResponse): ChatMessage {
		const payload = m.metadata?.payload as Record<string, unknown> | undefined;
		const chatType = (payload?.type as ChatMessage['type']) || 'status';

		switch (chatType) {
			case 'entities':
				return {
					id: m.id,
					type: 'entities',
					entity_type: (payload?.entity_type as EntityType) || 'product',
					entities: (payload?.entities as Array<Record<string, unknown>>) || [],
					errors:
						(payload?.errors as Array<{ field: string; message: string; severity: string }>) || [],
					timestamp: m.created_at,
				};
			case 'clarification':
				return {
					id: m.id,
					type: 'clarification',
					questions: (payload?.questions as ClarificationQuestion[]) || [],
					timestamp: m.created_at,
				};
			case 'user_decision':
				return {
					id: m.id,
					type: 'user_decision',
					decisions: (payload?.decisions as EntityDecision[]) || [],
					timestamp: m.created_at,
				};
			case 'user_clarification':
				return {
					id: m.id,
					type: 'user_clarification',
					answers: (payload?.answers as ClarificationAnswer[]) || [],
					timestamp: m.created_at,
				};
			case 'complete':
				return {
					id: m.id,
					type: 'complete',
					message: m.content,
					timestamp: m.created_at,
				};
			case 'error':
				return {
					id: m.id,
					type: 'error',
					message: m.content,
					timestamp: m.created_at,
				};
			default:
				return {
					id: m.id,
					type: 'status',
					step: (payload?.step as string) || '',
					message: m.content,
					timestamp: m.created_at,
				};
		}
	}

	clear() {
		this.disconnectWebSocket();
		this.messages = [];
		this.workflow = null;
		this.workflows = [];
		this.connectionState = 'disconnected';
		this.thinking = false;
		this.currentStep = '';
		this.loading = false;
		this.error = null;
		this.pendingEntities = null;
		this.pendingClarification = null;
		this.pendingDecisions = [];
		this.messageCounter = 0;
		this.restoredFromHistory = false;
	}
}

export const workflowStore = new WorkflowStore();
