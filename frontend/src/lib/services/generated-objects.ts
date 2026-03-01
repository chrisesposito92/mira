import type { ApiClient } from './api.js';
import type {
	GeneratedObject,
	GeneratedObjectUpdate,
	BulkStatusUpdate,
	CreateObjectPayload,
	PushResultResponse,
	BulkPushResultResponse,
	PushStatusResponse,
} from '$lib/types';

export interface GeneratedObjectService {
	listObjects(useCaseId: string, entityType?: string, status?: string): Promise<GeneratedObject[]>;
	getObject(objectId: string): Promise<GeneratedObject>;
	updateObject(objectId: string, data: GeneratedObjectUpdate): Promise<GeneratedObject>;
	bulkUpdateStatus(data: BulkStatusUpdate): Promise<{ message: string }>;
	createObject(useCaseId: string, data: CreateObjectPayload): Promise<GeneratedObject>;
	getTemplates(): Promise<Record<string, Record<string, unknown>>>;
	pushObject(objectId: string): Promise<PushResultResponse>;
	pushObjects(useCaseId: string, objectIds?: string[]): Promise<BulkPushResultResponse>;
	getPushStatus(useCaseId: string): Promise<PushStatusResponse>;
}

export function createGeneratedObjectService(client: ApiClient): GeneratedObjectService {
	return {
		listObjects: (useCaseId, entityType?, status?) => {
			const params = new URLSearchParams();
			if (entityType) params.set('entity_type', entityType);
			if (status) params.set('status', status);
			const qs = params.toString();
			return client.get<GeneratedObject[]>(
				`/api/use-cases/${useCaseId}/objects${qs ? `?${qs}` : ''}`,
			);
		},
		getObject: (objectId) => client.get<GeneratedObject>(`/api/objects/${objectId}`),
		updateObject: (objectId, data) =>
			client.patch<GeneratedObject>(`/api/objects/${objectId}`, data),
		bulkUpdateStatus: (data) => client.post<{ message: string }>('/api/objects/bulk-status', data),
		createObject: (useCaseId, data) =>
			client.post<GeneratedObject>(`/api/use-cases/${useCaseId}/objects`, data),
		getTemplates: () =>
			client.get<Record<string, Record<string, unknown>>>('/api/objects/templates'),
		pushObject: (objectId) => client.post<PushResultResponse>(`/api/objects/${objectId}/push`, {}),
		pushObjects: (useCaseId, objectIds?) =>
			client.post<BulkPushResultResponse>(
				`/api/use-cases/${useCaseId}/push`,
				objectIds ? { object_ids: objectIds } : {},
			),
		getPushStatus: (useCaseId) =>
			client.get<PushStatusResponse>(`/api/use-cases/${useCaseId}/push/status`),
	};
}
