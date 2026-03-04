import type { ApiClient } from './api.js';
import type { UseCase, UseCaseCreate, UseCaseUpdate } from '$lib/types';

export interface UseCaseService {
	list(projectId: string): Promise<UseCase[]>;
	get(id: string): Promise<UseCase>;
	create(projectId: string, data: UseCaseCreate): Promise<UseCase>;
	update(id: string, data: UseCaseUpdate): Promise<UseCase>;
	delete(id: string): Promise<void>;
	reset(id: string): Promise<{ message: string }>;
}

export function createUseCaseService(client: ApiClient): UseCaseService {
	return {
		list: (projectId) => client.get<UseCase[]>(`/api/projects/${projectId}/use-cases`),
		get: (id) => client.get<UseCase>(`/api/use-cases/${id}`),
		create: (projectId, data) => client.post<UseCase>(`/api/projects/${projectId}/use-cases`, data),
		update: (id, data) => client.patch<UseCase>(`/api/use-cases/${id}`, data),
		delete: (id) => client.delete(`/api/use-cases/${id}`),
		reset: (id) => client.post<{ message: string }>(`/api/use-cases/${id}/reset`, {}),
	};
}
