import type { ApiClient } from './api.js';
import type { Document } from '$lib/types';

export interface DocumentService {
	list(projectId: string): Promise<Document[]>;
	get(id: string): Promise<Document>;
	upload(projectId: string, file: File): Promise<Document>;
	uploadWithProgress(
		projectId: string,
		file: File,
		onProgress: (percent: number) => void,
	): Promise<Document>;
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
		uploadWithProgress: async (projectId, file, onProgress) => {
			const headers = await client.getAuthHeaders();
			return new Promise<Document>((resolve, reject) => {
				const formData = new FormData();
				formData.append('file', file);

				const xhr = new XMLHttpRequest();
				xhr.open('POST', `${client.baseUrl}/api/projects/${projectId}/documents`);

				for (const [key, value] of Object.entries(headers)) {
					xhr.setRequestHeader(key, value);
				}

				xhr.upload.onprogress = (e) => {
					if (e.lengthComputable) {
						onProgress(Math.round((e.loaded / e.total) * 100));
					}
				};

				xhr.onload = () => {
					if (xhr.status >= 200 && xhr.status < 300) {
						resolve(JSON.parse(xhr.responseText) as Document);
					} else {
						try {
							const body = JSON.parse(xhr.responseText);
							reject(new Error(body.detail ?? xhr.statusText));
						} catch {
							reject(new Error(xhr.statusText));
						}
					}
				};

				xhr.onerror = () => reject(new Error('Upload failed'));
				xhr.send(formData);
			});
		},
		delete: (id) => client.delete(`/api/documents/${id}`),
	};
}
