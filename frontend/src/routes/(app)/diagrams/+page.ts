import { createApiClient, createDiagramService, createProjectService } from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent, depends }) => {
	depends('app:diagrams');

	const { supabase, session } = await parent();
	const client = createApiClient(supabase, session?.access_token);
	const diagramService = createDiagramService(client);
	const projectService = createProjectService(client);

	const [diagrams, projects] = await Promise.allSettled([
		diagramService.list(),
		projectService.list(),
	]);

	return {
		diagrams: diagrams.status === 'fulfilled' ? diagrams.value : [],
		projects: projects.status === 'fulfilled' ? projects.value : [],
	};
};
