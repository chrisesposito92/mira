import type { DiagramListItem, DiagramCreate } from '$lib/types';
import type { DiagramService } from '$lib/services/diagrams.js';

class DiagramStore {
	diagrams = $state<DiagramListItem[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);

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
			// Append to list as a DiagramListItem (omit content/thumbnail)
			this.diagrams = [
				...this.diagrams,
				{
					id: diagram.id,
					user_id: diagram.user_id,
					customer_name: diagram.customer_name,
					title: diagram.title,
					project_id: diagram.project_id,
					schema_version: diagram.schema_version,
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

	clear() {
		this.diagrams = [];
		this.loading = false;
		this.error = null;
	}
}

export const diagramStore = new DiagramStore();
