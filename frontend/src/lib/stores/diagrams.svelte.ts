import type {
	Diagram,
	DiagramListItem,
	DiagramCreate,
	DiagramContent,
	DiagramConnection,
	DiagramSystem,
	ComponentLibraryItem,
} from '$lib/types';
import type { DiagramService } from '$lib/services/diagrams.js';

class DiagramStore {
	diagrams = $state<DiagramListItem[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);

	// Editor state
	currentDiagram = $state<Diagram | null>(null);
	componentLibrary = $state<ComponentLibraryItem[]>([]);
	saving = $state(false);

	sortedDiagrams = $derived(
		[...this.diagrams].sort(
			(a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
		),
	);

	async loadDiagrams(service: DiagramService) {
		this.loading = true;
		this.error = null;
		try {
			this.diagrams = await service.list();
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load diagrams';
		} finally {
			this.loading = false;
		}
	}

	async createDiagram(service: DiagramService, data: DiagramCreate) {
		this.error = null;
		try {
			const diagram = await service.create(data);
			// Append to list as a DiagramListItem (omit content)
			this.diagrams = [
				...this.diagrams,
				{
					id: diagram.id,
					user_id: diagram.user_id,
					customer_name: diagram.customer_name,
					title: diagram.title,
					project_id: diagram.project_id,
					schema_version: diagram.schema_version,
					thumbnail_base64: null,
					created_at: diagram.created_at,
					updated_at: diagram.updated_at,
				},
			];
			return diagram;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to create diagram';
			return null;
		}
	}

	async deleteDiagram(service: DiagramService, id: string) {
		this.error = null;
		try {
			await service.delete(id);
			this.diagrams = this.diagrams.filter((d) => d.id !== id);
			return true;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to delete diagram';
			return false;
		}
	}

	async loadDiagram(service: DiagramService, id: string) {
		this.loading = true;
		this.error = null;
		try {
			this.currentDiagram = await service.get(id);
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load diagram';
		} finally {
			this.loading = false;
		}
	}

	async loadComponentLibrary(service: DiagramService) {
		try {
			this.componentLibrary = await service.listComponents();
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load component library';
		}
	}

	async updateContent(service: DiagramService, content: DiagramContent) {
		if (!this.currentDiagram) return;
		this.saving = true;
		this.error = null;
		try {
			const updated = await service.update(this.currentDiagram.id, { content });
			this.currentDiagram = updated;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to save diagram';
		} finally {
			this.saving = false;
		}
	}

	removeSystem(systemId: string) {
		if (!this.currentDiagram) return;
		this.currentDiagram = {
			...this.currentDiagram,
			content: {
				...this.currentDiagram.content,
				systems: this.currentDiagram.content.systems.filter((s) => s.id !== systemId),
				connections: this.currentDiagram.content.connections.filter(
					(c) => c.source_id !== systemId && c.target_id !== systemId,
				),
			},
		};
	}

	addConnection(connection: DiagramConnection) {
		if (!this.currentDiagram) return;
		this.currentDiagram = {
			...this.currentDiagram,
			content: {
				...this.currentDiagram.content,
				connections: [...this.currentDiagram.content.connections, connection],
			},
		};
	}

	removeConnection(connectionId: string) {
		if (!this.currentDiagram) return;
		this.currentDiagram = {
			...this.currentDiagram,
			content: {
				...this.currentDiagram.content,
				connections: this.currentDiagram.content.connections.filter((c) => c.id !== connectionId),
			},
		};
	}

	updateConnection(connectionId: string, updates: Partial<DiagramConnection>) {
		if (!this.currentDiagram) return;
		this.currentDiagram = {
			...this.currentDiagram,
			content: {
				...this.currentDiagram.content,
				connections: this.currentDiagram.content.connections.map((c) =>
					c.id === connectionId ? { ...c, ...updates } : c,
				),
			},
		};
	}

	addSystem(system: DiagramSystem) {
		if (!this.currentDiagram) return;
		this.currentDiagram = {
			...this.currentDiagram,
			content: {
				...this.currentDiagram.content,
				systems: [...this.currentDiagram.content.systems, system],
			},
		};
	}

	clearEditor() {
		this.currentDiagram = null;
		this.componentLibrary = [];
		this.saving = false;
	}

	clear() {
		this.diagrams = [];
		this.loading = false;
		this.error = null;
		this.clearEditor();
	}
}

export const diagramStore = new DiagramStore();
