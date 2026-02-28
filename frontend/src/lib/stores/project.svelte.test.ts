import { describe, it, expect, vi, beforeEach } from 'vitest';

// Fresh instance per test — import the class, not the singleton
let store: any;

beforeEach(async () => {
	// Dynamic import to get fresh module (stores use $state which is module-level)
	const mod = await import('./project.svelte.js');
	// Use the singleton but reset it
	store = mod.projectStore;
	store.clear();
});

function mockProjectService(overrides = {}) {
	return {
		list: vi.fn().mockResolvedValue([
			{ id: '1', name: 'P1', updated_at: '2024-01-01T00:00:00Z' },
			{ id: '2', name: 'P2', updated_at: '2024-06-01T00:00:00Z' },
		]),
		get: vi.fn().mockResolvedValue({ id: '1', name: 'P1' }),
		create: vi.fn().mockResolvedValue({ id: '3', name: 'New', updated_at: '2024-07-01T00:00:00Z' }),
		update: vi
			.fn()
			.mockResolvedValue({ id: '1', name: 'Updated', updated_at: '2024-08-01T00:00:00Z' }),
		delete: vi.fn().mockResolvedValue(undefined),
		...overrides,
	} as any;
}

function mockUseCaseService(overrides = {}) {
	return {
		list: vi.fn().mockResolvedValue([]),
		create: vi
			.fn()
			.mockResolvedValue({ id: 'uc1', title: 'UC', updated_at: '2024-01-01T00:00:00Z' }),
		update: vi.fn().mockResolvedValue({ id: 'uc1', title: 'Updated UC' }),
		delete: vi.fn().mockResolvedValue(undefined),
		...overrides,
	} as any;
}

function mockDocumentService(overrides = {}) {
	return {
		list: vi.fn().mockResolvedValue([]),
		upload: vi.fn().mockResolvedValue({ id: 'd1', filename: 'test.pdf' }),
		delete: vi.fn().mockResolvedValue(undefined),
		...overrides,
	} as any;
}

describe('ProjectStore', () => {
	it('initializes with empty state', () => {
		expect(store.projects).toEqual([]);
		expect(store.currentProject).toBeNull();
		expect(store.loading).toBe(false);
		expect(store.error).toBeNull();
	});

	it('loadProjects populates projects', async () => {
		const service = mockProjectService();
		await store.loadProjects(service);
		expect(store.projects).toHaveLength(2);
		expect(service.list).toHaveBeenCalledOnce();
	});

	it('loadProjects sets error on failure', async () => {
		const service = mockProjectService({
			list: vi.fn().mockRejectedValue(new Error('Network error')),
		});
		await store.loadProjects(service);
		expect(store.error).toBe('Network error');
		expect(store.projects).toEqual([]);
	});

	it('createProject adds to projects', async () => {
		const service = mockProjectService();
		const result = await store.createProject(service, { name: 'New' });
		expect(result).toBeTruthy();
		expect(store.projects).toHaveLength(1);
		expect(store.projects[0].name).toBe('New');
	});

	it('updateProject updates in-place', async () => {
		store.projects = [{ id: '1', name: 'Old' }];
		store.currentProject = { id: '1', name: 'Old' };
		const service = mockProjectService();
		await store.updateProject(service, '1', { name: 'Updated' });
		expect(store.projects[0].name).toBe('Updated');
		expect(store.currentProject.name).toBe('Updated');
	});

	it('deleteProject removes from list', async () => {
		store.projects = [
			{ id: '1', name: 'P1' },
			{ id: '2', name: 'P2' },
		];
		store.currentProject = { id: '1', name: 'P1' };
		const service = mockProjectService();
		const ok = await store.deleteProject(service, '1');
		expect(ok).toBe(true);
		expect(store.projects).toHaveLength(1);
		expect(store.currentProject).toBeNull();
	});

	it('sortedProjects orders by updated_at desc', async () => {
		const service = mockProjectService();
		await store.loadProjects(service);
		expect(store.sortedProjects[0].id).toBe('2'); // newer
	});

	it('clear resets all state', async () => {
		const service = mockProjectService();
		await store.loadProjects(service);
		store.clear();
		expect(store.projects).toEqual([]);
		expect(store.currentProject).toBeNull();
		expect(store.useCases).toEqual([]);
		expect(store.documents).toEqual([]);
	});

	// Use case tests
	it('createUseCase adds to useCases', async () => {
		const service = mockUseCaseService();
		const uc = await store.createUseCase(service, 'proj1', { title: 'UC' });
		expect(uc).toBeTruthy();
		expect(store.useCases).toHaveLength(1);
	});

	it('deleteUseCase removes from list', async () => {
		store.useCases = [{ id: 'uc1' }, { id: 'uc2' }];
		const service = mockUseCaseService();
		await store.deleteUseCase(service, 'uc1');
		expect(store.useCases).toHaveLength(1);
	});

	// Document tests
	it('uploadDocument adds to documents', async () => {
		const service = mockDocumentService();
		const doc = await store.uploadDocument(service, 'proj1', new File([''], 'test.pdf'));
		expect(doc).toBeTruthy();
		expect(store.documents).toHaveLength(1);
	});

	it('deleteDocument removes from list', async () => {
		store.documents = [{ id: 'd1' }, { id: 'd2' }];
		const service = mockDocumentService();
		await store.deleteDocument(service, 'd1');
		expect(store.documents).toHaveLength(1);
	});
});
