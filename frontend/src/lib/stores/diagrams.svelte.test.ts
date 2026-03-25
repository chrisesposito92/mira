import { describe, it, expect, vi, beforeEach } from 'vitest';

import type {
	Diagram,
	DiagramContent,
	DiagramConnection,
	DiagramSystem,
	ComponentLibraryItem,
} from '$lib/types';

// Fresh state per test via singleton reset
let store: any;

beforeEach(async () => {
	const mod = await import('./diagrams.svelte.js');
	store = mod.diagramStore;
	store.clear();
});

function makeDiagramContent(overrides: Partial<DiagramContent> = {}): DiagramContent {
	return {
		systems: [],
		connections: [],
		settings: { background_color: '#1a1a2e', show_labels: true },
		...overrides,
	};
}

function makeDiagram(overrides: Partial<Diagram> = {}): Diagram {
	return {
		id: 'diag-1',
		user_id: 'user-1',
		customer_name: 'Acme Corp',
		title: 'Integration Diagram',
		project_id: null,
		content: makeDiagramContent(),
		schema_version: 1,
		thumbnail_base64: null,
		created_at: '2024-01-01T00:00:00Z',
		updated_at: '2024-01-01T00:00:00Z',
		...overrides,
	};
}

function makeSystem(overrides: Partial<DiagramSystem> = {}): DiagramSystem {
	return {
		id: 'sys-1',
		component_library_id: 'comp-1',
		name: 'Salesforce',
		logo_base64: null,
		x: 100,
		y: 200,
		category: 'crm',
		...overrides,
	};
}

function makeComponentLibraryItem(
	overrides: Partial<ComponentLibraryItem> = {},
): ComponentLibraryItem {
	return {
		id: 'comp-1',
		slug: 'salesforce',
		name: 'Salesforce',
		domain: 'CRM',
		category: 'front_office',
		logo_base64: null,
		is_native_connector: true,
		display_order: 1,
		created_at: '2024-01-01T00:00:00Z',
		...overrides,
	};
}

function mockDiagramService(overrides = {}) {
	return {
		list: vi.fn().mockResolvedValue([]),
		get: vi.fn().mockResolvedValue(makeDiagram()),
		create: vi.fn().mockResolvedValue(makeDiagram()),
		update: vi.fn().mockResolvedValue(makeDiagram()),
		delete: vi.fn().mockResolvedValue(undefined),
		listComponents: vi.fn().mockResolvedValue([makeComponentLibraryItem()]),
		...overrides,
	} as any;
}

describe('DiagramStore - editor extension', () => {
	it('loadDiagram sets currentDiagram to the fetched diagram', async () => {
		const diagram = makeDiagram({ id: 'diag-42' });
		const service = mockDiagramService({ get: vi.fn().mockResolvedValue(diagram) });
		await store.loadDiagram(service, 'diag-42');
		expect(store.currentDiagram).toEqual(diagram);
		expect(service.get).toHaveBeenCalledWith('diag-42');
	});

	it('loadDiagram sets loading to true during fetch, false after', async () => {
		let resolveGet: (d: Diagram) => void;
		const pendingGet = new Promise<Diagram>((r) => (resolveGet = r));
		const service = mockDiagramService({ get: vi.fn().mockReturnValue(pendingGet) });

		const loadPromise = store.loadDiagram(service, 'diag-1');
		expect(store.loading).toBe(true);

		resolveGet!(makeDiagram());
		await loadPromise;
		expect(store.loading).toBe(false);
	});

	it('loadDiagram sets error on service failure', async () => {
		const service = mockDiagramService({
			get: vi.fn().mockRejectedValue(new Error('Not found')),
		});
		await store.loadDiagram(service, 'diag-missing');
		expect(store.error).toBe('Not found');
		expect(store.currentDiagram).toBeNull();
	});

	it('loadComponentLibrary populates componentLibrary array', async () => {
		const items = [makeComponentLibraryItem({ id: 'c1' }), makeComponentLibraryItem({ id: 'c2' })];
		const service = mockDiagramService({
			listComponents: vi.fn().mockResolvedValue(items),
		});
		await store.loadComponentLibrary(service);
		expect(store.componentLibrary).toEqual(items);
		expect(store.componentLibrary).toHaveLength(2);
	});

	it('updateContent calls service.update() with the diagram id and new content', async () => {
		const original = makeDiagram({ id: 'diag-1' });
		const newContent = makeDiagramContent({
			systems: [makeSystem()],
		});
		const updated = makeDiagram({ id: 'diag-1', content: newContent });
		const service = mockDiagramService({
			update: vi.fn().mockResolvedValue(updated),
		});

		store.currentDiagram = original;
		await store.updateContent(service, newContent);

		expect(service.update).toHaveBeenCalledWith('diag-1', { content: newContent });
	});

	it('updateContent updates currentDiagram.content on success', async () => {
		const newContent = makeDiagramContent({ systems: [makeSystem()] });
		const updated = makeDiagram({ content: newContent });
		const service = mockDiagramService({
			update: vi.fn().mockResolvedValue(updated),
		});

		store.currentDiagram = makeDiagram();
		await store.updateContent(service, newContent);

		expect(store.currentDiagram.content.systems).toHaveLength(1);
		expect(store.currentDiagram).toEqual(updated);
	});

	it('updateContent sets saving to true during save, false after', async () => {
		let resolveUpdate: (d: Diagram) => void;
		const pendingUpdate = new Promise<Diagram>((r) => (resolveUpdate = r));
		const service = mockDiagramService({ update: vi.fn().mockReturnValue(pendingUpdate) });

		store.currentDiagram = makeDiagram();
		const updatePromise = store.updateContent(service, makeDiagramContent());
		expect(store.saving).toBe(true);

		resolveUpdate!(makeDiagram());
		await updatePromise;
		expect(store.saving).toBe(false);
	});

	it('addSystem appends a system to currentDiagram.content.systems', () => {
		store.currentDiagram = makeDiagram();
		expect(store.currentDiagram.content.systems).toHaveLength(0);

		const sys = makeSystem({ id: 'sys-new', name: 'Stripe' });
		store.addSystem(sys);

		expect(store.currentDiagram.content.systems).toHaveLength(1);
		expect(store.currentDiagram.content.systems[0].name).toBe('Stripe');
	});

	it('clearEditor resets currentDiagram to null and componentLibrary to empty', async () => {
		store.currentDiagram = makeDiagram();
		store.componentLibrary = [makeComponentLibraryItem()];
		store.saving = true;

		store.clearEditor();

		expect(store.currentDiagram).toBeNull();
		expect(store.componentLibrary).toEqual([]);
		expect(store.saving).toBe(false);
	});

	it('clear() also resets editor state (currentDiagram, componentLibrary, saving)', async () => {
		// Set up both list state and editor state
		store.diagrams = [
			{
				id: 'diag-1',
				user_id: 'u1',
				customer_name: 'Test',
				title: 'T',
				project_id: null,
				schema_version: 1,
				created_at: '2024-01-01T00:00:00Z',
				updated_at: '2024-01-01T00:00:00Z',
			},
		];
		store.currentDiagram = makeDiagram();
		store.componentLibrary = [makeComponentLibraryItem()];
		store.saving = true;

		store.clear();

		// List state reset
		expect(store.diagrams).toEqual([]);
		expect(store.loading).toBe(false);
		expect(store.error).toBeNull();
		// Editor state reset -- addresses review MEDIUM concern
		expect(store.currentDiagram).toBeNull();
		expect(store.componentLibrary).toEqual([]);
		expect(store.saving).toBe(false);
	});

	it('updateContent sets error and returns without crash when currentDiagram is null', async () => {
		const service = mockDiagramService();
		store.currentDiagram = null;

		// Should not throw
		await store.updateContent(service, makeDiagramContent());

		expect(service.update).not.toHaveBeenCalled();
		expect(store.saving).toBe(false);
	});
});

function makeConnection(overrides: Partial<DiagramConnection> = {}): DiagramConnection {
	return {
		id: 'conn-1',
		source_id: 'sys-1',
		target_id: 'sys-2',
		label: 'Usage Events',
		direction: 'unidirectional',
		connection_type: 'api',
		...overrides,
	};
}

describe('DiagramStore - connection CRUD', () => {
	it('removeSystem filters out the system from content.systems', () => {
		const sys1 = makeSystem({ id: 'sys-1' });
		const sys2 = makeSystem({ id: 'sys-2', name: 'Stripe' });
		store.currentDiagram = makeDiagram({
			content: makeDiagramContent({ systems: [sys1, sys2] }),
		});

		store.removeSystem('sys-1');

		expect(store.currentDiagram.content.systems).toHaveLength(1);
		expect(store.currentDiagram.content.systems[0].id).toBe('sys-2');
	});

	it('removeSystem also removes connections referencing the removed system (cascade)', () => {
		const sys1 = makeSystem({ id: 'sys-1' });
		const sys2 = makeSystem({ id: 'sys-2', name: 'Stripe' });
		const conn1 = makeConnection({ id: 'conn-1', source_id: 'sys-1', target_id: 'sys-2' });
		const conn2 = makeConnection({ id: 'conn-2', source_id: 'sys-2', target_id: 'sys-3' });
		store.currentDiagram = makeDiagram({
			content: makeDiagramContent({ systems: [sys1, sys2], connections: [conn1, conn2] }),
		});

		store.removeSystem('sys-1');

		expect(store.currentDiagram.content.systems).toHaveLength(1);
		expect(store.currentDiagram.content.connections).toHaveLength(1);
		expect(store.currentDiagram.content.connections[0].id).toBe('conn-2');
	});

	it('removeSystem is a no-op when currentDiagram is null', () => {
		store.currentDiagram = null;
		expect(() => store.removeSystem('sys-1')).not.toThrow();
		expect(store.currentDiagram).toBeNull();
	});

	it('addConnection appends a connection to content.connections', () => {
		store.currentDiagram = makeDiagram();
		expect(store.currentDiagram.content.connections).toHaveLength(0);

		const conn = makeConnection();
		store.addConnection(conn);

		expect(store.currentDiagram.content.connections).toHaveLength(1);
		expect(store.currentDiagram.content.connections[0].label).toBe('Usage Events');
	});

	it('addConnection is a no-op when currentDiagram is null', () => {
		store.currentDiagram = null;
		expect(() => store.addConnection(makeConnection())).not.toThrow();
		expect(store.currentDiagram).toBeNull();
	});

	it('removeConnection filters out the connection by id', () => {
		const conn1 = makeConnection({ id: 'conn-1' });
		const conn2 = makeConnection({ id: 'conn-2', label: 'Billing Data' });
		store.currentDiagram = makeDiagram({
			content: makeDiagramContent({ connections: [conn1, conn2] }),
		});

		store.removeConnection('conn-1');

		expect(store.currentDiagram.content.connections).toHaveLength(1);
		expect(store.currentDiagram.content.connections[0].id).toBe('conn-2');
	});

	it('removeConnection is a no-op when currentDiagram is null', () => {
		store.currentDiagram = null;
		expect(() => store.removeConnection('conn-1')).not.toThrow();
		expect(store.currentDiagram).toBeNull();
	});

	it('updateConnection merges partial updates into matching connection', () => {
		const conn = makeConnection({ id: 'conn-1', label: 'Old Label' });
		store.currentDiagram = makeDiagram({
			content: makeDiagramContent({ connections: [conn] }),
		});

		store.updateConnection('conn-1', { label: 'New Label', direction: 'bidirectional' });

		const updated = store.currentDiagram.content.connections[0];
		expect(updated.label).toBe('New Label');
		expect(updated.direction).toBe('bidirectional');
		expect(updated.source_id).toBe('sys-1'); // unchanged
	});

	it('updateConnection preserves other connections untouched', () => {
		const conn1 = makeConnection({ id: 'conn-1', label: 'First' });
		const conn2 = makeConnection({ id: 'conn-2', label: 'Second' });
		store.currentDiagram = makeDiagram({
			content: makeDiagramContent({ connections: [conn1, conn2] }),
		});

		store.updateConnection('conn-1', { label: 'Updated' });

		expect(store.currentDiagram.content.connections[0].label).toBe('Updated');
		expect(store.currentDiagram.content.connections[1].label).toBe('Second');
	});

	it('updateConnection is a no-op when currentDiagram is null', () => {
		store.currentDiagram = null;
		expect(() => store.updateConnection('conn-1', { label: 'X' })).not.toThrow();
		expect(store.currentDiagram).toBeNull();
	});
});

describe('DiagramStore - existing methods preserved', () => {
	it('loadDiagrams still works', async () => {
		const service = mockDiagramService({
			list: vi.fn().mockResolvedValue([
				{
					id: '1',
					user_id: 'u1',
					customer_name: 'C1',
					title: 'T1',
					project_id: null,
					schema_version: 1,
					created_at: '2024-01-01T00:00:00Z',
					updated_at: '2024-01-01T00:00:00Z',
				},
			]),
		});
		await store.loadDiagrams(service);
		expect(store.diagrams).toHaveLength(1);
	});

	it('createDiagram still works', async () => {
		const service = mockDiagramService();
		const result = await store.createDiagram(service, { customer_name: 'Acme' });
		expect(result).toBeTruthy();
		expect(store.diagrams).toHaveLength(1);
	});

	it('deleteDiagram still works', async () => {
		store.diagrams = [
			{
				id: 'diag-1',
				user_id: 'u1',
				customer_name: 'C1',
				title: 'T1',
				project_id: null,
				schema_version: 1,
				created_at: '2024-01-01T00:00:00Z',
				updated_at: '2024-01-01T00:00:00Z',
			},
		];
		const service = mockDiagramService();
		const ok = await store.deleteDiagram(service, 'diag-1');
		expect(ok).toBe(true);
		expect(store.diagrams).toHaveLength(0);
	});
});
