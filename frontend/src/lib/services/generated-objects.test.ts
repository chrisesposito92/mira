import { describe, it, expect, vi } from 'vitest';
import { createGeneratedObjectService } from './generated-objects.js';
import type { ApiClient } from './api.js';

function mockClient(): ApiClient {
	return {
		get: vi.fn().mockResolvedValue([]),
		post: vi.fn().mockResolvedValue({ message: 'ok' }),
		patch: vi.fn().mockResolvedValue({ id: '1', name: 'Updated' }),
		delete: vi.fn().mockResolvedValue(undefined),
		upload: vi.fn(),
	} as unknown as ApiClient;
}

describe('GeneratedObjectService', () => {
	it('listObjects calls GET /api/use-cases/:id/objects without filters', async () => {
		const client = mockClient();
		const service = createGeneratedObjectService(client);
		await service.listObjects('uc-1');
		expect(client.get).toHaveBeenCalledWith('/api/use-cases/uc-1/objects');
	});

	it('listObjects calls GET with entity_type and status filters', async () => {
		const client = mockClient();
		const service = createGeneratedObjectService(client);
		await service.listObjects('uc-1', 'meter', 'approved');
		expect(client.get).toHaveBeenCalledWith(
			'/api/use-cases/uc-1/objects?entity_type=meter&status=approved',
		);
	});

	it('listObjects builds query string with only entity_type', async () => {
		const client = mockClient();
		const service = createGeneratedObjectService(client);
		await service.listObjects('uc-1', 'product');
		expect(client.get).toHaveBeenCalledWith('/api/use-cases/uc-1/objects?entity_type=product');
	});

	it('getObject calls GET /api/objects/:id', async () => {
		const client = mockClient();
		const service = createGeneratedObjectService(client);
		await service.getObject('obj-1');
		expect(client.get).toHaveBeenCalledWith('/api/objects/obj-1');
	});

	it('updateObject calls PATCH /api/objects/:id', async () => {
		const client = mockClient();
		const service = createGeneratedObjectService(client);
		await service.updateObject('obj-1', { name: 'New Name' });
		expect(client.patch).toHaveBeenCalledWith('/api/objects/obj-1', { name: 'New Name' });
	});

	it('bulkUpdateStatus calls POST /api/objects/bulk-status', async () => {
		const client = mockClient();
		const service = createGeneratedObjectService(client);
		await service.bulkUpdateStatus({ ids: ['a', 'b'], status: 'approved' });
		expect(client.post).toHaveBeenCalledWith('/api/objects/bulk-status', {
			ids: ['a', 'b'],
			status: 'approved',
		});
	});
});
