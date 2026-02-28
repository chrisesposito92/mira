import type { ApiClient } from './api.js';
import type { Document } from '$lib/types';

export interface DocumentService {
	list(projectId: string): Promise<Document[]>;
	get(id: string): Promise<Document>;
	upload(projectId: string, file: File): Promise<Document>;
	delete(id: string): Promise<void>;
}

export function createDocumentService(client: ApiClient): DocumentService {
	return {
		list: (projectId) => client.get<Document[]>(`/api/projects/${projectId}/documents`),
		get: (id) => client.get<Document>(`/api/documents/${id}`),
		upload: (projectId, file) => {
			const formData = new FormData();
			formData.append('file', file);
			return client.upload<Document>(`/api/projects/${projectId}/documents`, formData);
		},
		delete: (id) => client.delete(`/api/documents/${id}`),
	};
}
