import { error } from '@sveltejs/kit';
import {
	createApiClient,
	createUseCaseService,
	createProjectService,
	createGeneratedObjectService,
} from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent, params }) => {
	const { supabase, session } = await parent();
	const client = createApiClient(supabase, session?.access_token);
	const useCaseService = createUseCaseService(client);
	const projectService = createProjectService(client);
	const objectService = createGeneratedObjectService(client);

	// Fetch all three in parallel — use case is required, others are graceful
	const [useCaseResult, project, objects] = await Promise.allSettled([
		useCaseService.get(params.useCaseId),
		projectService.get(params.projectId),
		objectService.listObjects(params.useCaseId),
	]);

	if (useCaseResult.status === 'rejected') {
		error(404, 'Use case not found');
	}

	return {
		useCase: useCaseResult.value,
		project: project.status === 'fulfilled' ? project.value : null,
		objects: objects.status === 'fulfilled' ? objects.value : [],
	};
};
