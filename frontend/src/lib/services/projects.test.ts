import { describe, it, expect, vi } from 'vitest';
import { createProjectService } from './projects.js';
import type { ApiClient } from './api.js';

function mockClient(): ApiClient {
	return {
		get: vi.fn().mockResolvedValue([]),
		post: vi.fn().mockResolvedValue({ id: '1', name: 'Test' }),
		patch: vi.fn().mockResolvedValue({ id: '1', name: 'Updated' }),
		delete: vi.fn().mockResolvedValue(undefined),
		upload: vi.fn(),
	} as unknown as ApiClient;
}

describe('ProjectService', () => {
	it('list calls GET /api/projects', async () => {
		const client = mockClient();
		const service = createProjectService(client);
		await service.list();
		expect(client.get).toHaveBeenCalledWith('/api/projects');
	});

	it('get calls GET /api/projects/:id', async () => {
		const client = mockClient();
		const service = createProjectService(client);
		await service.get('abc');
		expect(client.get).toHaveBeenCalledWith('/api/projects/abc');
	});

	it('create calls POST /api/projects', async () => {
		const client = mockClient();
		const service = createProjectService(client);
		await service.create({ name: 'Test' });
		expect(client.post).toHaveBeenCalledWith('/api/projects', { name: 'Test' });
	});

	it('update calls PATCH /api/projects/:id', async () => {
		const client = mockClient();
		const service = createProjectService(client);
		await service.update('abc', { name: 'Updated' });
		expect(client.patch).toHaveBeenCalledWith('/api/projects/abc', { name: 'Updated' });
	});

	it('delete calls DELETE /api/projects/:id', async () => {
		const client = mockClient();
		const service = createProjectService(client);
		await service.delete('abc');
		expect(client.delete).toHaveBeenCalledWith('/api/projects/abc');
	});
});
