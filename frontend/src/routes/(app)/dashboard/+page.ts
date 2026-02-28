import { createApiClient, createProjectService, createOrgConnectionService } from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent, depends }) => {
	depends('app:projects');

	const { supabase, session } = await parent();
	const client = createApiClient(supabase, session?.access_token);
	const projectService = createProjectService(client);
	const orgConnectionService = createOrgConnectionService(client);

	const [projects, connections] = await Promise.allSettled([
		projectService.list(),
		orgConnectionService.list(),
	]);

	return {
		projects: projects.status === 'fulfilled' ? projects.value : [],
		connections: connections.status === 'fulfilled' ? connections.value : [],
	};
};
