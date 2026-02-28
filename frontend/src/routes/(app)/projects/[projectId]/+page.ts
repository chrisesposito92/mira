import {
	createApiClient,
	createProjectService,
	createUseCaseService,
	createDocumentService,
	createOrgConnectionService,
} from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent, params }) => {
	const { supabase } = await parent();
	const client = createApiClient(supabase);
	const projectService = createProjectService(client);
	const useCaseService = createUseCaseService(client);
	const documentService = createDocumentService(client);
	const orgConnectionService = createOrgConnectionService(client);

	const [project, useCases, documents, connections] = await Promise.all([
		projectService.get(params.projectId),
		useCaseService.list(params.projectId),
		documentService.list(params.projectId),
		orgConnectionService.list(),
	]);

	return { project, useCases, documents, connections, supabase };
};
