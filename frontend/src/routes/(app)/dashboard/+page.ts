import { createApiClient, createProjectService, createOrgConnectionService } from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent }) => {
	const { supabase } = await parent();
	const client = createApiClient(supabase);
	const projectService = createProjectService(client);
	const orgConnectionService = createOrgConnectionService(client);

	const [projects, connections] = await Promise.all([
		projectService.list(),
		orgConnectionService.list(),
	]);

	return { projects, connections, supabase };
};
