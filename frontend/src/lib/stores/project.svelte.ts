import type {
	Project,
	ProjectCreate,
	ProjectUpdate,
	UseCase,
	UseCaseCreate,
	UseCaseUpdate,
	Document,
} from '$lib/types';
import type { ProjectService } from '$lib/services/projects.js';
import type { UseCaseService } from '$lib/services/use-cases.js';
import type { DocumentService } from '$lib/services/documents.js';

class ProjectStore {
	projects = $state<Project[]>([]);
	currentProject = $state<Project | null>(null);
	useCases = $state<UseCase[]>([]);
	documents = $state<Document[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);

	sortedProjects = $derived(
		[...this.projects].sort(
			(a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
		),
	);

	sortedUseCases = $derived(
		[...this.useCases].sort(
			(a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
		),
	);

	async loadProjects(service: ProjectService) {
		this.loading = true;
		this.error = null;
		try {
			this.projects = await service.list();
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load projects';
		} finally {
			this.loading = false;
		}
	}

	async loadProject(service: ProjectService, id: string) {
		this.loading = true;
		this.error = null;
		try {
			this.currentProject = await service.get(id);
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load project';
		} finally {
			this.loading = false;
		}
	}

	async createProject(service: ProjectService, data: ProjectCreate) {
		this.error = null;
		try {
			const project = await service.create(data);
			this.projects = [...this.projects, project];
			return project;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to create project';
			return null;
		}
	}

	async updateProject(service: ProjectService, id: string, data: ProjectUpdate) {
		this.error = null;
		try {
			const updated = await service.update(id, data);
			this.projects = this.projects.map((p) => (p.id === id ? updated : p));
			if (this.currentProject?.id === id) this.currentProject = updated;
			return updated;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to update project';
			return null;
		}
	}

	async deleteProject(service: ProjectService, id: string) {
		this.error = null;
		try {
			await service.delete(id);
			this.projects = this.projects.filter((p) => p.id !== id);
			if (this.currentProject?.id === id) this.currentProject = null;
			return true;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to delete project';
			return false;
		}
	}

	// --- Use Cases ---

	async loadUseCases(service: UseCaseService, projectId: string) {
		this.loading = true;
		this.error = null;
		try {
			this.useCases = await service.list(projectId);
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load use cases';
		} finally {
			this.loading = false;
		}
	}

	async createUseCase(service: UseCaseService, projectId: string, data: UseCaseCreate) {
		this.error = null;
		try {
			const uc = await service.create(projectId, data);
			this.useCases = [...this.useCases, uc];
			return uc;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to create use case';
			return null;
		}
	}

	async updateUseCase(service: UseCaseService, id: string, data: UseCaseUpdate) {
		this.error = null;
		try {
			const updated = await service.update(id, data);
			this.useCases = this.useCases.map((uc) => (uc.id === id ? updated : uc));
			return updated;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to update use case';
			return null;
		}
	}

	async deleteUseCase(service: UseCaseService, id: string) {
		this.error = null;
		try {
			await service.delete(id);
			this.useCases = this.useCases.filter((uc) => uc.id !== id);
			return true;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to delete use case';
			return false;
		}
	}

	// --- Documents ---

	async loadDocuments(service: DocumentService, projectId: string) {
		this.loading = true;
		this.error = null;
		try {
			this.documents = await service.list(projectId);
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load documents';
		} finally {
			this.loading = false;
		}
	}

	async uploadDocument(service: DocumentService, projectId: string, file: File) {
		this.error = null;
		try {
			const doc = await service.upload(projectId, file);
			this.documents = [...this.documents, doc];
			return doc;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to upload document';
			return null;
		}
	}

	async deleteDocument(service: DocumentService, id: string) {
		this.error = null;
		try {
			await service.delete(id);
			this.documents = this.documents.filter((d) => d.id !== id);
			return true;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to delete document';
			return false;
		}
	}

	clear() {
		this.projects = [];
		this.currentProject = null;
		this.useCases = [];
		this.documents = [];
		this.loading = false;
		this.error = null;
	}
}

export const projectStore = new ProjectStore();
