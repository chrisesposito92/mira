import { error } from '@sveltejs/kit';
import {
	createApiClient,
	createProjectService,
	createUseCaseService,
	createDocumentService,
	createOrgConnectionService,
} from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent, params, depends }) => {
	depends('app:project');

	const { supabase, session } = await parent();
	const client = createApiClient(supabase, session?.access_token);
	const projectService = createProjectService(client);
	const useCaseService = createUseCaseService(client);
	const documentService = createDocumentService(client);
	const orgConnectionService = createOrgConnectionService(client);

	// Project is required — fail the page if it can't load
	let project;
	try {
		project = await projectService.get(params.projectId);
	} catch {
		error(404, 'Project not found');
	}

	// Secondary data can fail gracefully
	const [useCases, documents, connections] = await Promise.allSettled([
		useCaseService.list(params.projectId),
		documentService.list(params.projectId),
		orgConnectionService.list(),
	]);

	return {
		project,
		session,
		useCases: useCases.status === 'fulfilled' ? useCases.value : [],
		documents: documents.status === 'fulfilled' ? documents.value : [],
		connections: connections.status === 'fulfilled' ? connections.value : [],
	};
};
