import type { ApiClient } from './api.js';
import type {
	OrgConnection,
	OrgConnectionCreate,
	OrgConnectionUpdate,
	OrgConnectionTestResult,
} from '$lib/types';

export interface OrgConnectionService {
	list(): Promise<OrgConnection[]>;
	get(id: string): Promise<OrgConnection>;
	create(data: OrgConnectionCreate): Promise<OrgConnection>;
	update(id: string, data: OrgConnectionUpdate): Promise<OrgConnection>;
	delete(id: string): Promise<void>;
	test(id: string): Promise<OrgConnectionTestResult>;
}

export function createOrgConnectionService(client: ApiClient): OrgConnectionService {
	return {
		list: () => client.get<OrgConnection[]>('/api/org-connections'),
		get: (id) => client.get<OrgConnection>(`/api/org-connections/${id}`),
		create: (data) => client.post<OrgConnection>('/api/org-connections', data),
		update: (id, data) => client.patch<OrgConnection>(`/api/org-connections/${id}`, data),
		delete: (id) => client.delete(`/api/org-connections/${id}`),
		test: (id) => client.post<OrgConnectionTestResult>(`/api/org-connections/${id}/test`, {}),
	};
}
