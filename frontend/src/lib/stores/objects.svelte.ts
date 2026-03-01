import { SvelteSet } from 'svelte/reactivity';
import type { GeneratedObject, GeneratedObjectUpdate, EntityType, ObjectStatus } from '$lib/types';
import type { GeneratedObjectService } from '$lib/services/generated-objects.js';

// Entity type push order for tree grouping (exported for reuse in components)
export const ENTITY_TYPE_ORDER: EntityType[] = [
	'product',
	'meter',
	'aggregation',
	'compound_aggregation',
	'plan_template',
	'plan',
	'pricing',
	'account',
	'account_plan',
	'measurement',
];

// Object statuses (exported for reuse in filter dropdowns)
export const OBJECT_STATUSES: ObjectStatus[] = [
	'draft',
	'approved',
	'rejected',
	'pushed',
	'push_failed',
];

export interface EntityGroup {
	entityType: EntityType;
	objects: GeneratedObject[];
}

class ObjectsStore {
	objects = $state<GeneratedObject[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);
	saving = $state(false);
	selectedObjectId = $state<string | null>(null);
	selectedIds = $state(new SvelteSet<string>());
	filterEntityType = $state<EntityType | ''>('');
	filterStatus = $state<ObjectStatus | ''>('');
	searchQuery = $state('');

	filteredObjects = $derived.by(() => {
		let result = this.objects;
		if (this.filterEntityType) {
			result = result.filter((o) => o.entity_type === this.filterEntityType);
		}
		if (this.filterStatus) {
			result = result.filter((o) => o.status === this.filterStatus);
		}
		if (this.searchQuery) {
			const q = this.searchQuery.toLowerCase();
			result = result.filter(
				(o) =>
					(o.name?.toLowerCase().includes(q) ?? false) ||
					(o.code?.toLowerCase().includes(q) ?? false),
			);
		}
		return result;
	});

	tree = $derived.by(() => {
		const grouped: Partial<Record<EntityType, GeneratedObject[]>> = {};
		for (const o of this.filteredObjects) {
			(grouped[o.entity_type] ??= []).push(o);
		}
		return ENTITY_TYPE_ORDER.filter((et) => grouped[et]).map((et) => ({
			entityType: et,
			objects: grouped[et]!,
		}));
	});

	selectedObject = $derived(this.objects.find((o) => o.id === this.selectedObjectId) ?? null);

	async loadObjects(service: GeneratedObjectService, useCaseId: string) {
		this.loading = true;
		this.error = null;
		try {
			this.objects = await service.listObjects(useCaseId);
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load objects';
		} finally {
			this.loading = false;
		}
	}

	async updateObject(
		service: GeneratedObjectService,
		objectId: string,
		data: GeneratedObjectUpdate,
	) {
		this.saving = true;
		this.error = null;
		try {
			const updated = await service.updateObject(objectId, data);
			this.objects = this.objects.map((o) => (o.id === objectId ? updated : o));
			return updated;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to update object';
			return null;
		} finally {
			this.saving = false;
		}
	}

	async bulkUpdateStatus(service: GeneratedObjectService, ids: string[], status: ObjectStatus) {
		this.saving = true;
		this.error = null;
		try {
			await service.bulkUpdateStatus({ ids, status });
			const idSet = new Set(ids);
			this.objects = this.objects.map((o) => (idSet.has(o.id) ? { ...o, status } : o));
			this.selectedIds.clear();
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to bulk update';
		} finally {
			this.saving = false;
		}
	}

	selectObject(id: string | null) {
		this.selectedObjectId = id;
	}

	toggleSelection(id: string) {
		if (this.selectedIds.has(id)) {
			this.selectedIds.delete(id);
		} else {
			this.selectedIds.add(id);
		}
	}

	selectAll() {
		this.selectedIds.clear();
		for (const o of this.filteredObjects) this.selectedIds.add(o.id);
	}

	clearSelection() {
		this.selectedIds.clear();
	}

	clear() {
		this.objects = [];
		this.loading = false;
		this.error = null;
		this.saving = false;
		this.selectedObjectId = null;
		this.selectedIds.clear();
		this.filterEntityType = '';
		this.filterStatus = '';
		this.searchQuery = '';
	}
}

export const objectsStore = new ObjectsStore();
