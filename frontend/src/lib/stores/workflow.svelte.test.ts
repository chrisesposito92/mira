import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { WsServerMessage, ChatMessage, ChatMessageResponse } from '$lib/types';

let store: any;

beforeEach(async () => {
	const mod = await import('./workflow.svelte.js');
	store = mod.workflowStore;
	store.clear();
});

function mockWorkflowService(overrides = {}) {
	return {
		list: vi.fn().mockResolvedValue([]),
		get: vi.fn().mockResolvedValue({ id: 'wf-1', status: 'running' }),
		start: vi.fn().mockResolvedValue({
			id: 'wf-1',
			use_case_id: 'uc-1',
			workflow_type: 'product_meter_aggregation',
			status: 'running',
			thread_id: 'th-1',
			interrupt_payload: null,
			error_message: null,
			started_at: '2024-01-01T00:00:00Z',
			completed_at: null,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
		}),
		listModels: vi
			.fn()
			.mockResolvedValue([
				{ id: 'claude-sonnet-4-6', provider: 'anthropic', display_name: 'Claude Sonnet 4.6' },
			]),
		listMessages: vi.fn().mockResolvedValue([]),
		saveMessage: vi.fn().mockResolvedValue({ id: 'm1' }),
		...overrides,
	} as any;
}

describe('WorkflowStore', () => {
	it('initializes with empty state', () => {
		expect(store.messages).toEqual([]);
		expect(store.workflow).toBeNull();
		expect(store.workflows).toEqual([]);
		expect(store.models).toEqual([]);
		expect(store.connectionState).toBe('disconnected');
		expect(store.thinking).toBe(false);
		expect(store.currentStep).toBe('');
		expect(store.loading).toBe(false);
		expect(store.error).toBeNull();
		expect(store.pendingEntities).toBeNull();
		expect(store.pendingClarification).toBeNull();
		expect(store.pendingDecisions).toEqual([]);
	});

	it('loadModels populates models', async () => {
		const service = mockWorkflowService();
		await store.loadModels(service);
		expect(store.models).toHaveLength(1);
		expect(store.models[0].id).toBe('claude-sonnet-4-6');
		expect(service.listModels).toHaveBeenCalledOnce();
	});

	it('loadModels sets error on failure', async () => {
		const service = mockWorkflowService({
			listModels: vi.fn().mockRejectedValue(new Error('Network error')),
		});
		await store.loadModels(service);
		expect(store.error).toBe('Network error');
	});

	it('loadWorkflows populates workflows', async () => {
		const service = mockWorkflowService({
			list: vi.fn().mockResolvedValue([
				{ id: 'wf-1', status: 'running' },
				{ id: 'wf-2', status: 'completed' },
			]),
		});
		await store.loadWorkflows(service, 'uc-1');
		expect(store.workflows).toHaveLength(2);
		expect(service.list).toHaveBeenCalledWith('uc-1');
	});

	it('loadWorkflows sets error on failure', async () => {
		const service = mockWorkflowService({
			list: vi.fn().mockRejectedValue(new Error('Failed')),
		});
		await store.loadWorkflows(service, 'uc-1');
		expect(store.error).toBe('Failed');
	});

	// handleWsMessage tests
	it('handleWsMessage status sets thinking and adds message', () => {
		const msg: WsServerMessage = {
			type: 'status',
			step: 'analyzing',
			message: 'Analyzing use case...',
		};
		store.handleWsMessage(msg);
		expect(store.thinking).toBe(true);
		expect(store.currentStep).toBe('analyzing');
		expect(store.messages).toHaveLength(1);
		expect(store.messages[0].type).toBe('status');
		expect(store.messages[0].step).toBe('analyzing');
		expect(store.messages[0].message).toBe('Analyzing use case...');
	});

	it('handleWsMessage entities stops thinking and sets pendingEntities', () => {
		const msg: WsServerMessage = {
			type: 'entities',
			entity_type: 'product',
			entities: [{ name: 'API Calls' }],
			errors: [],
		};
		store.thinking = true;
		store.handleWsMessage(msg);
		expect(store.thinking).toBe(false);
		expect(store.pendingEntities).toEqual({
			entity_type: 'product',
			entities: [{ name: 'API Calls' }],
		});
		expect(store.pendingDecisions).toEqual([]);
		expect(store.messages).toHaveLength(1);
		expect(store.messages[0].type).toBe('entities');
		expect(store.messages[0].entity_type).toBe('product');
	});

	it('handleWsMessage clarification sets pendingClarification', () => {
		const msg: WsServerMessage = {
			type: 'clarification',
			questions: [
				{
					id: 'q1',
					question: 'Billing frequency?',
					options: [{ id: 'o1', label: 'Monthly' }],
					allows_free_text: false,
				},
			],
		};
		store.thinking = true;
		store.handleWsMessage(msg);
		expect(store.thinking).toBe(false);
		expect(store.pendingClarification).toHaveLength(1);
		expect(store.pendingClarification![0].id).toBe('q1');
		expect(store.messages).toHaveLength(1);
		expect(store.messages[0].type).toBe('clarification');
	});

	it('handleWsMessage complete marks workflow completed', () => {
		store.workflow = { id: 'wf-1', status: 'running' };
		const msg: WsServerMessage = {
			type: 'complete',
			message: 'All done!',
		};
		store.handleWsMessage(msg);
		expect(store.thinking).toBe(false);
		expect(store.currentStep).toBe('');
		expect(store.pendingEntities).toBeNull();
		expect(store.pendingClarification).toBeNull();
		expect(store.workflow!.status).toBe('completed');
		expect(store.messages).toHaveLength(1);
		expect(store.messages[0].type).toBe('complete');
	});

	it('handleWsMessage error marks workflow failed', () => {
		store.workflow = { id: 'wf-1', status: 'running' };
		const msg: WsServerMessage = {
			type: 'error',
			message: 'Something went wrong',
		};
		store.handleWsMessage(msg);
		expect(store.thinking).toBe(false);
		expect(store.workflow!.status).toBe('failed');
		expect(store.messages).toHaveLength(1);
		expect(store.messages[0].type).toBe('error');
		expect(store.messages[0].message).toBe('Something went wrong');
	});

	// submitDecision tests
	it('submitDecision accumulates decisions', () => {
		store.pendingEntities = {
			entity_type: 'product',
			entities: [{ name: 'A' }, { name: 'B' }],
		};

		store.submitDecision({ entity_index: 0, decision: 'approved' });
		expect(store.pendingDecisions).toHaveLength(1);
		// Not yet all decided, so pendingEntities should still be set
		expect(store.pendingEntities).not.toBeNull();
	});

	// submitClarificationAnswers test
	it('submitClarificationAnswers sends and clears', () => {
		// Set up a mock ws
		store.ws = { send: vi.fn(), disconnect: vi.fn() };
		store.pendingClarification = [
			{
				id: 'q1',
				question: 'Billing?',
				options: [],
				allows_free_text: true,
			},
		];

		const answers = [{ question_id: 'q1', free_text: 'Monthly' }];
		store.submitClarificationAnswers(answers);

		expect(store.ws.send).toHaveBeenCalledWith({
			type: 'clarify',
			answers,
		});
		expect(store.thinking).toBe(true);
		expect(store.pendingClarification).toBeNull();
		expect(store.messages).toHaveLength(1);
		expect(store.messages[0].type).toBe('user_clarification');
		expect(store.messages[0].answers).toEqual(answers);
	});

	it('submitClarificationAnswers does nothing without ws', () => {
		store.pendingClarification = [
			{ id: 'q1', question: 'test?', options: [], allows_free_text: false },
		];
		// ws is null by default after clear()
		store.submitClarificationAnswers([{ question_id: 'q1', selected_option: 'o1' }]);
		// Should not crash, and should not add a message
		expect(store.messages).toEqual([]);
	});

	it('clear resets all state', () => {
		// Populate some state
		store.messages = [{ id: 'msg-1', type: 'status' } as ChatMessage];
		store.workflow = { id: 'wf-1', status: 'running' };
		store.workflows = [{ id: 'wf-1' }];
		store.thinking = true;
		store.currentStep = 'generating';
		store.loading = true;
		store.error = 'some error';
		store.pendingEntities = { entity_type: 'product', entities: [] };
		store.pendingClarification = [];
		store.pendingDecisions = [{ entity_index: 0, decision: 'approved' }];

		store.clear();

		expect(store.messages).toEqual([]);
		expect(store.workflow).toBeNull();
		expect(store.workflows).toEqual([]);
		expect(store.connectionState).toBe('disconnected');
		expect(store.thinking).toBe(false);
		expect(store.currentStep).toBe('');
		expect(store.loading).toBe(false);
		expect(store.error).toBeNull();
		expect(store.pendingEntities).toBeNull();
		expect(store.pendingClarification).toBeNull();
		expect(store.pendingDecisions).toEqual([]);
	});

	it('loadMessages converts persisted messages to ChatMessages', async () => {
		const persisted: ChatMessageResponse[] = [
			{
				id: 'm1',
				workflow_id: 'wf-1',
				role: 'assistant',
				content: 'Analyzing...',
				metadata: { payload: { type: 'status', step: 'analyzing' } },
				created_at: '2024-01-01T00:00:00Z',
			},
			{
				id: 'm2',
				workflow_id: 'wf-1',
				role: 'assistant',
				content: 'All done!',
				metadata: { payload: { type: 'complete' } },
				created_at: '2024-01-01T00:01:00Z',
			},
		];
		const service = mockWorkflowService({
			listMessages: vi.fn().mockResolvedValue(persisted),
		});
		await store.loadMessages(service, 'wf-1');
		expect(store.messages).toHaveLength(2);
		expect(store.messages[0].type).toBe('status');
		expect(store.messages[0].step).toBe('analyzing');
		expect(store.messages[1].type).toBe('complete');
	});

	it('loadMessages sets error on failure', async () => {
		const service = mockWorkflowService({
			listMessages: vi.fn().mockRejectedValue(new Error('Load failed')),
		});
		await store.loadMessages(service, 'wf-1');
		expect(store.error).toBe('Load failed');
	});
});
