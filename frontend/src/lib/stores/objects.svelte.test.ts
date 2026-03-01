import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SvelteSet } from 'svelte/reactivity';

type ObjectsStore = Awaited<typeof import('./objects.svelte.js')>['objectsStore'];
let store: ObjectsStore;

beforeEach(async () => {
	const mod = await import('./objects.svelte.js');
	store = mod.objectsStore;
	store.clear();
});

function makeMockObject(
	overrides: Partial<import('$lib/types').GeneratedObject> = {},
): import('$lib/types').GeneratedObject {
	return {
		id: 'obj-1',
		use_case_id: 'uc-1',
		entity_type: 'product',
		name: 'Test Product',
		code: 'test_product',
		status: 'draft',
		data: { name: 'Test' },
		validation_errors: null,
		m3ter_id: null,
		depends_on: null,
		created_at: '2024-01-01T00:00:00Z',
		updated_at: '2024-01-01T00:00:00Z',
		...overrides,
	};
}

function mockObjectService(
	overrides = {},
): import('$lib/services/generated-objects.js').GeneratedObjectService {
	return {
		listObjects: vi.fn().mockResolvedValue([
			makeMockObject({ id: 'obj-1', entity_type: 'product', name: 'Product A' }),
			makeMockObject({ id: 'obj-2', entity_type: 'meter', name: 'Meter A', code: 'meter_a' }),
			makeMockObject({
				id: 'obj-3',
				entity_type: 'aggregation',
				name: 'Agg A',
				status: 'approved',
			}),
		]),
		getObject: vi.fn().mockResolvedValue(makeMockObject()),
		updateObject: vi
			.fn()
			.mockResolvedValue(makeMockObject({ id: 'obj-1', name: 'Updated Product' })),
		bulkUpdateStatus: vi.fn().mockResolvedValue({ message: 'ok' }),
		...overrides,
	};
}

describe('ObjectsStore', () => {
	it('initializes with empty state', () => {
		expect(store.objects).toEqual([]);
		expect(store.loading).toBe(false);
		expect(store.error).toBeNull();
		expect(store.saving).toBe(false);
		expect(store.selectedObjectId).toBeNull();
		expect(store.selectedIds.size).toBe(0);
		expect(store.filterEntityType).toBe('');
		expect(store.filterStatus).toBe('');
		expect(store.searchQuery).toBe('');
	});

	it('loadObjects populates objects', async () => {
		const service = mockObjectService();
		await store.loadObjects(service, 'uc-1');
		expect(store.objects).toHaveLength(3);
		expect(service.listObjects).toHaveBeenCalledWith('uc-1');
	});

	it('loadObjects sets error on failure', async () => {
		const service = mockObjectService({
			listObjects: vi.fn().mockRejectedValue(new Error('Network error')),
		});
		await store.loadObjects(service, 'uc-1');
		expect(store.error).toBe('Network error');
		expect(store.objects).toEqual([]);
	});

	it('tree groups objects by entity type', async () => {
		const service = mockObjectService();
		await store.loadObjects(service, 'uc-1');
		expect(store.tree).toHaveLength(3);
		expect(store.tree[0].entityType).toBe('product');
		expect(store.tree[1].entityType).toBe('meter');
		expect(store.tree[2].entityType).toBe('aggregation');
	});

	it('tree follows entity push order', async () => {
		store.objects = [
			makeMockObject({ id: 'obj-1', entity_type: 'pricing' }),
			makeMockObject({ id: 'obj-2', entity_type: 'product' }),
			makeMockObject({ id: 'obj-3', entity_type: 'meter' }),
		];
		const types = store.tree.map((g) => g.entityType);
		expect(types).toEqual(['product', 'meter', 'pricing']);
	});

	it('filteredObjects filters by entity type', async () => {
		const service = mockObjectService();
		await store.loadObjects(service, 'uc-1');
		store.filterEntityType = 'meter';
		expect(store.filteredObjects).toHaveLength(1);
		expect(store.filteredObjects[0].entity_type).toBe('meter');
	});

	it('filteredObjects filters by status', async () => {
		const service = mockObjectService();
		await store.loadObjects(service, 'uc-1');
		store.filterStatus = 'approved';
		expect(store.filteredObjects).toHaveLength(1);
		expect(store.filteredObjects[0].status).toBe('approved');
	});

	it('filteredObjects filters by search query on name and code', async () => {
		const service = mockObjectService();
		await store.loadObjects(service, 'uc-1');
		store.searchQuery = 'meter';
		expect(store.filteredObjects).toHaveLength(1);
		expect(store.filteredObjects[0].name).toBe('Meter A');

		store.searchQuery = 'meter_a';
		expect(store.filteredObjects).toHaveLength(1);
		expect(store.filteredObjects[0].code).toBe('meter_a');
	});

	it('selectedObject returns correct object', () => {
		store.objects = [
			makeMockObject({ id: 'obj-1' }),
			makeMockObject({ id: 'obj-2', name: 'Second' }),
		];
		store.selectedObjectId = 'obj-2';
		expect(store.selectedObject).toBeTruthy();
		expect(store.selectedObject!.name).toBe('Second');
	});

	it('toggleSelection adds and removes from selectedIds', () => {
		store.toggleSelection('obj-1');
		expect(store.selectedIds.has('obj-1')).toBe(true);
		store.toggleSelection('obj-1');
		expect(store.selectedIds.has('obj-1')).toBe(false);
	});

	it('selectAll selects all filtered objects', async () => {
		const service = mockObjectService();
		await store.loadObjects(service, 'uc-1');
		store.selectAll();
		expect(store.selectedIds.size).toBe(3);
	});

	it('clearSelection empties selectedIds', () => {
		store.selectedIds = new SvelteSet(['obj-1', 'obj-2']);
		store.clearSelection();
		expect(store.selectedIds.size).toBe(0);
	});

	it('updateObject updates in-place', async () => {
		store.objects = [makeMockObject({ id: 'obj-1', name: 'Old' })];
		const service = mockObjectService();
		const result = await store.updateObject(service, 'obj-1', { name: 'Updated Product' });
		expect(result.ok).toBe(true);
		expect(store.objects[0].name).toBe('Updated Product');
	});

	it('bulkUpdateStatus updates multiple objects and clears selection', async () => {
		store.objects = [
			makeMockObject({ id: 'obj-1', status: 'draft' }),
			makeMockObject({ id: 'obj-2', status: 'draft' }),
			makeMockObject({ id: 'obj-3', status: 'draft' }),
		];
		store.selectedIds = new SvelteSet(['obj-1', 'obj-2']);
		const service = mockObjectService();
		await store.bulkUpdateStatus(service, ['obj-1', 'obj-2'], 'approved');
		expect(store.objects[0].status).toBe('approved');
		expect(store.objects[1].status).toBe('approved');
		expect(store.objects[2].status).toBe('draft');
		expect(store.selectedIds.size).toBe(0);
	});

	it('clear resets all state', async () => {
		const service = mockObjectService();
		await store.loadObjects(service, 'uc-1');
		store.selectedObjectId = 'obj-1';
		store.selectedIds = new SvelteSet(['obj-1']);
		store.filterEntityType = 'meter';
		store.filterStatus = 'approved';
		store.searchQuery = 'test';
		store.clear();
		expect(store.objects).toEqual([]);
		expect(store.loading).toBe(false);
		expect(store.error).toBeNull();
		expect(store.saving).toBe(false);
		expect(store.selectedObjectId).toBeNull();
		expect(store.selectedIds.size).toBe(0);
		expect(store.filterEntityType).toBe('');
		expect(store.filterStatus).toBe('');
		expect(store.searchQuery).toBe('');
	});
});
