import { describe, it, expect, vi, beforeEach } from 'vitest';

let store: any;

beforeEach(async () => {
	const mod = await import('./org-connections.svelte.js');
	store = mod.orgConnectionStore;
	store.clear();
});

function mockService(overrides = {}) {
	return {
		list: vi.fn().mockResolvedValue([
			{ id: '1', org_name: 'Org A', status: 'active' },
			{ id: '2', org_name: 'Org B', status: 'inactive' },
		]),
		create: vi.fn().mockResolvedValue({ id: '3', org_name: 'New Org', status: 'inactive' }),
		update: vi.fn().mockResolvedValue({ id: '1', org_name: 'Updated Org' }),
		delete: vi.fn().mockResolvedValue(undefined),
		test: vi.fn().mockResolvedValue({
			success: true,
			message: 'Connection successful',
			tested_at: '2024-01-01T00:00:00Z',
		}),
		...overrides,
	} as any;
}

describe('OrgConnectionStore', () => {
	it('initializes with empty state', () => {
		expect(store.connections).toEqual([]);
		expect(store.loading).toBe(false);
		expect(store.error).toBeNull();
		expect(store.testResult).toBeNull();
		expect(store.testing).toBe(false);
	});

	it('loadConnections populates connections', async () => {
		const service = mockService();
		await store.loadConnections(service);
		expect(store.connections).toHaveLength(2);
		expect(service.list).toHaveBeenCalledOnce();
	});

	it('loadConnections sets error on failure', async () => {
		const service = mockService({
			list: vi.fn().mockRejectedValue(new Error('Failed')),
		});
		await store.loadConnections(service);
		expect(store.error).toBe('Failed');
	});

	it('createConnection adds to connections', async () => {
		const service = mockService();
		const conn = await store.createConnection(service, {
			org_id: 'org-3',
			org_name: 'New Org',
			client_id: 'cid',
			client_secret: 'csec',
		});
		expect(conn).toBeTruthy();
		expect(store.connections).toHaveLength(1);
	});

	it('updateConnection updates in-place', async () => {
		store.connections = [{ id: '1', org_name: 'Old' }];
		const service = mockService();
		await store.updateConnection(service, '1', { org_name: 'Updated Org' });
		expect(store.connections[0].org_name).toBe('Updated Org');
	});

	it('deleteConnection removes from list', async () => {
		store.connections = [{ id: '1' }, { id: '2' }];
		const service = mockService();
		const ok = await store.deleteConnection(service, '1');
		expect(ok).toBe(true);
		expect(store.connections).toHaveLength(1);
	});

	it('testConnection sets testResult and updates status on success', async () => {
		store.connections = [{ id: '1', status: 'inactive', last_tested_at: null }];
		const service = mockService();
		const result = await store.testConnection(service, '1');
		expect(result?.success).toBe(true);
		expect(store.testResult?.success).toBe(true);
		expect(store.connections[0].status).toBe('active');
		expect(store.testing).toBe(false);
	});

	it('testConnection sets error on failure', async () => {
		const service = mockService({
			test: vi.fn().mockRejectedValue(new Error('Connection refused')),
		});
		const result = await store.testConnection(service, '1');
		expect(result).toBeNull();
		expect(store.error).toBe('Connection refused');
		expect(store.testing).toBe(false);
	});

	it('clear resets all state', async () => {
		const service = mockService();
		await store.loadConnections(service);
		store.clear();
		expect(store.connections).toEqual([]);
		expect(store.testResult).toBeNull();
	});
});
