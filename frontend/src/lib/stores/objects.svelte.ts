import { SvelteSet } from 'svelte/reactivity';
import type {
	GeneratedObject,
	GeneratedObjectUpdate,
	CreateObjectPayload,
	EntityType,
	ObjectStatus,
	PushSession,
	PushWsMessage,
	PushObjectProgress,
} from '$lib/types';
import type { GeneratedObjectService } from '$lib/services/generated-objects.js';
import { PushWebSocketClient } from '$lib/services/push-websocket.js';

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

// Statuses eligible for push (matches backend _PUSHABLE_STATUSES)
export const PUSHABLE_STATUSES: ReadonlySet<ObjectStatus> = new SvelteSet<ObjectStatus>([
	'approved',
	'push_failed',
]);

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
	pushSession = $state<PushSession | null>(null);
	pushing = $state(false);
	private _pushWs: PushWebSocketClient | null = null;

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

	pushableSelectedIds = $derived.by(() => {
		const objById = new Map(this.objects.map((o) => [o.id, o]));
		const pushable = new SvelteSet<string>();
		for (const id of this.selectedIds) {
			const obj = objById.get(id);
			if (obj && PUSHABLE_STATUSES.has(obj.status)) {
				pushable.add(id);
			}
		}
		return pushable;
	});

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
	): Promise<{ ok: true; updated: GeneratedObject } | { ok: false; error: string }> {
		this.saving = true;
		this.error = null;
		try {
			const updated = await service.updateObject(objectId, data);
			this.objects = this.objects.map((o) => (o.id === objectId ? updated : o));
			return { ok: true, updated };
		} catch (e) {
			const msg = e instanceof Error ? e.message : 'Failed to update object';
			this.error = msg;
			return { ok: false, error: msg };
		} finally {
			this.saving = false;
		}
	}

	async bulkUpdateStatus(
		service: GeneratedObjectService,
		ids: string[],
		status: ObjectStatus,
	): Promise<{ ok: true } | { ok: false; error: string }> {
		this.saving = true;
		this.error = null;
		try {
			await service.bulkUpdateStatus({ ids, status });
			const idSet = new Set(ids);
			this.objects = this.objects.map((o) => (idSet.has(o.id) ? { ...o, status } : o));
			this.selectedIds.clear();
			return { ok: true };
		} catch (e) {
			const msg = e instanceof Error ? e.message : 'Failed to bulk update';
			this.error = msg;
			return { ok: false, error: msg };
		} finally {
			this.saving = false;
		}
	}

	async createObject(
		service: GeneratedObjectService,
		useCaseId: string,
		payload: CreateObjectPayload,
	): Promise<{ ok: true; created: GeneratedObject } | { ok: false; error: string }> {
		this.saving = true;
		this.error = null;
		try {
			const created = await service.createObject(useCaseId, payload);
			this.objects = [created, ...this.objects];
			this.selectedObjectId = created.id;
			return { ok: true, created };
		} catch (e) {
			const msg = e instanceof Error ? e.message : 'Failed to create object';
			this.error = msg;
			return { ok: false, error: msg };
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

	async pushSingleObject(
		service: GeneratedObjectService,
		objectId: string,
	): Promise<{ ok: true; m3terId: string } | { ok: false; error: string }> {
		this.pushing = true;
		try {
			const result = await service.pushObject(objectId);
			if (result.success) {
				// Re-fetch from server to get authoritative DB state
				// (prevents stale data from concurrent effects overwriting the status)
				try {
					const refreshed = await service.getObject(objectId);
					this.objects = this.objects.map((o) => (o.id === objectId ? refreshed : o));
				} catch {
					// Fallback to local update if re-fetch fails
					this.objects = this.objects.map((o) =>
						o.id === objectId
							? { ...o, status: 'pushed' as const, m3ter_id: result.m3ter_id ?? null }
							: o,
					);
				}
				return { ok: true, m3terId: result.m3ter_id ?? '' };
			} else {
				this.objects = this.objects.map((o) =>
					o.id === objectId ? { ...o, status: 'push_failed' as const } : o,
				);
				return { ok: false, error: result.error ?? 'Push failed' };
			}
		} catch (e) {
			const msg = e instanceof Error ? e.message : 'Push failed';
			this.objects = this.objects.map((o) =>
				o.id === objectId ? { ...o, status: 'push_failed' as const } : o,
			);
			return { ok: false, error: msg };
		} finally {
			this.pushing = false;
		}
	}

	startBulkPush(useCaseId: string, objectIds: string[], token: string): void {
		const items: PushObjectProgress[] = objectIds.map((id) => {
			const obj = this.objects.find((o) => o.id === id);
			return {
				entityId: id,
				entityType: obj?.entity_type ?? 'unknown',
				status: 'pending' as const,
			};
		});

		this.pushSession = {
			active: true,
			total: objectIds.length,
			completed: 0,
			succeeded: 0,
			failed: 0,
			items,
		};
		this.pushing = true;

		this._pushWs?.disconnect();
		this._pushWs = new PushWebSocketClient(
			(msg) => this.handlePushMessage(msg),
			() => {
				// WS closed — if session is still active, leave it (server continues)
			},
		);
		this._pushWs.connect(useCaseId, token, () => {
			// Send start_push command once the WebSocket connection is open
			this._pushWs?.send({ type: 'start_push', object_ids: objectIds });
		});
	}

	handlePushMessage(msg: PushWsMessage): void {
		if (!this.pushSession) return;

		switch (msg.type) {
			case 'push_started': {
				// Sort items by entity type push order so the first 'pushing' spinner
				// matches the backend's actual push sequence (not user selection order).
				const orderMap = new Map(ENTITY_TYPE_ORDER.map((et, i) => [et, i]));
				const sorted = [...this.pushSession.items].sort(
					(a, b) =>
						(orderMap.get(a.entityType as EntityType) ?? 99) -
						(orderMap.get(b.entityType as EntityType) ?? 99),
				);
				const startItems = sorted.map((item, i) =>
					i === 0 && item.status === 'pending' ? { ...item, status: 'pushing' as const } : item,
				);
				this.pushSession = { ...this.pushSession, total: msg.total, items: startItems };
				break;
			}

			case 'push_progress': {
				// Update the completed item's final status, then mark the next pending item as 'pushing'
				let markedNext = false;
				const updatedItems = this.pushSession.items.map((item) => {
					if (item.entityId === msg.entity_id) {
						return {
							...item,
							status: (msg.success ? 'pushed' : 'push_failed') as 'pushed' | 'push_failed',
							m3terId: msg.m3ter_id ?? undefined,
							error: msg.error ?? undefined,
						};
					}
					if (!markedNext && item.status === 'pending') {
						markedNext = true;
						return { ...item, status: 'pushing' as const };
					}
					return item;
				});
				this.pushSession = {
					...this.pushSession,
					completed: msg.completed,
					total: msg.total,
					succeeded: this.pushSession.succeeded + (msg.success ? 1 : 0),
					failed: this.pushSession.failed + (msg.success ? 0 : 1),
					items: updatedItems,
				};
				// Update the object in local state
				this.objects = this.objects.map((o) =>
					o.id === msg.entity_id
						? {
								...o,
								status: msg.success ? ('pushed' as const) : ('push_failed' as const),
								m3ter_id: msg.m3ter_id ?? o.m3ter_id,
							}
						: o,
				);
				break;
			}

			case 'push_complete':
				this.pushSession = {
					...this.pushSession,
					active: false,
					completed: msg.total,
					succeeded: msg.succeeded,
					failed: msg.failed,
				};
				this.pushing = false;
				this._pushWs?.disconnect();
				break;

			case 'push_error':
				this.pushSession = {
					...this.pushSession,
					active: false,
				};
				this.pushing = false;
				this.error = msg.message;
				this._pushWs?.disconnect();
				break;
		}
	}

	dismissPushSession(): void {
		this.pushSession = null;
		this._pushWs?.disconnect();
		this._pushWs = null;
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
		this.pushSession = null;
		this.pushing = false;
		this._pushWs?.disconnect();
		this._pushWs = null;
	}
}

export const objectsStore = new ObjectsStore();
