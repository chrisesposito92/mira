import type { ApiClient } from './api.js';
import type { GeneratedObject, GeneratedObjectUpdate, BulkStatusUpdate } from '$lib/types';

export interface GeneratedObjectService {
	listObjects(useCaseId: string, entityType?: string, status?: string): Promise<GeneratedObject[]>;
	getObject(objectId: string): Promise<GeneratedObject>;
	updateObject(objectId: string, data: GeneratedObjectUpdate): Promise<GeneratedObject>;
	bulkUpdateStatus(data: BulkStatusUpdate): Promise<{ message: string }>;
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
	};
}
