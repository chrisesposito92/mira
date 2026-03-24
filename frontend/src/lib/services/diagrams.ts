import type { ApiClient } from "./api.js";
import type {
	Diagram,
	DiagramListItem,
	DiagramCreate,
	DiagramUpdate,
	ComponentLibraryItem,
} from "$lib/types";

export interface DiagramService {
	list(): Promise<DiagramListItem[]>;
	get(id: string): Promise<Diagram>;
	create(data: DiagramCreate): Promise<Diagram>;
	update(id: string, data: DiagramUpdate): Promise<Diagram>;
	delete(id: string): Promise<void>;
	listComponents(): Promise<ComponentLibraryItem[]>;
}

export function createDiagramService(client: ApiClient): DiagramService {
	return {
		list: () => client.get<DiagramListItem[]>("/api/diagrams"),
		get: (id) => client.get<Diagram>(`/api/diagrams/${id}`),
		create: (data) => client.post<Diagram>("/api/diagrams", data),
		update: (id, data) => client.patch<Diagram>(`/api/diagrams/${id}`, data),
		delete: (id) => client.delete(`/api/diagrams/${id}`),
		listComponents: () =>
			client.get<ComponentLibraryItem[]>("/api/component-library"),
	};
}
