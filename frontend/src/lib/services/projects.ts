import type { ApiClient } from './api.js';
import type { Project, ProjectCreate, ProjectUpdate } from '$lib/types';

export interface ProjectService {
	list(): Promise<Project[]>;
	get(id: string): Promise<Project>;
	create(data: ProjectCreate): Promise<Project>;
	update(id: string, data: ProjectUpdate): Promise<Project>;
	delete(id: string): Promise<void>;
}

export function createProjectService(client: ApiClient): ProjectService {
	return {
		list: () => client.get<Project[]>('/api/projects'),
		get: (id) => client.get<Project>(`/api/projects/${id}`),
		create: (data) => client.post<Project>('/api/projects', data),
		update: (id, data) => client.patch<Project>(`/api/projects/${id}`, data),
		delete: (id) => client.delete(`/api/projects/${id}`),
	};
}
