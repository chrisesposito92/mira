import { error } from '@sveltejs/kit';
import {
	createApiClient,
	createUseCaseService,
	createProjectService,
	createWorkflowService,
} from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent, params }) => {
	const { supabase, session } = await parent();
	const client = createApiClient(supabase, session?.access_token);
	const useCaseService = createUseCaseService(client);
	const projectService = createProjectService(client);
	const workflowService = createWorkflowService(client);

	// Use case is required
	let useCase;
	try {
		useCase = await useCaseService.get(params.useCaseId);
	} catch {
		error(404, 'Use case not found');
	}

	// Secondary data can fail gracefully
	const [project, workflows, models] = await Promise.allSettled([
		projectService.get(params.projectId),
		workflowService.list(params.useCaseId),
		workflowService.listModels(),
	]);

	// Find any interrupted workflow
	const workflowList = workflows.status === 'fulfilled' ? workflows.value : [];
	const interruptedWorkflow = workflowList.find((w) => w.status === 'interrupted');

	// Load messages for interrupted workflow
	let interruptedMessages: Awaited<ReturnType<typeof workflowService.listMessages>> = [];
	if (interruptedWorkflow) {
		try {
			interruptedMessages = await workflowService.listMessages(interruptedWorkflow.id);
		} catch {
			// Graceful failure
		}
	}

	return {
		useCase,
		project: project.status === 'fulfilled' ? project.value : null,
		workflows: workflowList,
		models: models.status === 'fulfilled' ? models.value : [],
		interruptedWorkflow: interruptedWorkflow ?? null,
		interruptedMessages,
		session,
	};
};
