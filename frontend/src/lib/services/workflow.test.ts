import { describe, it, expect, vi } from 'vitest';
import { createWorkflowService } from './workflow.js';
import type { ApiClient } from './api.js';

function mockClient(): ApiClient {
	return {
		get: vi.fn().mockResolvedValue([]),
		post: vi.fn().mockResolvedValue({ id: '1', status: 'pending' }),
		patch: vi.fn().mockResolvedValue({}),
		delete: vi.fn().mockResolvedValue(undefined),
		upload: vi.fn(),
	} as unknown as ApiClient;
}

describe('WorkflowService', () => {
	it('list calls GET /api/use-cases/:id/workflows', async () => {
		const client = mockClient();
		const service = createWorkflowService(client);
		await service.list('uc-1');
		expect(client.get).toHaveBeenCalledWith('/api/use-cases/uc-1/workflows');
	});

	it('get calls GET /api/workflows/:id', async () => {
		const client = mockClient();
		const service = createWorkflowService(client);
		await service.get('wf-1');
		expect(client.get).toHaveBeenCalledWith('/api/workflows/wf-1');
	});

	it('start calls POST /api/use-cases/:id/workflows/start with model_id', async () => {
		const client = mockClient();
		const service = createWorkflowService(client);
		await service.start('uc-1', 'claude-sonnet-4-6');
		expect(client.post).toHaveBeenCalledWith('/api/use-cases/uc-1/workflows/start', {
			model_id: 'claude-sonnet-4-6',
		});
	});

	it('listModels calls GET /api/models', async () => {
		const client = mockClient();
		const service = createWorkflowService(client);
		await service.listModels();
		expect(client.get).toHaveBeenCalledWith('/api/models');
	});

	it('listMessages calls GET /api/workflows/:id/messages', async () => {
		const client = mockClient();
		const service = createWorkflowService(client);
		await service.listMessages('wf-1');
		expect(client.get).toHaveBeenCalledWith('/api/workflows/wf-1/messages');
	});

	it('saveMessage calls POST /api/workflows/:id/messages with body', async () => {
		const client = mockClient();
		const service = createWorkflowService(client);
		const data = { role: 'user' as const, content: 'hello', metadata: { payload: {} } };
		await service.saveMessage('wf-1', data);
		expect(client.post).toHaveBeenCalledWith('/api/workflows/wf-1/messages', data);
	});
});
