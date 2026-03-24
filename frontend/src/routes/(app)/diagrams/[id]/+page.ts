import { createApiClient, createDiagramService } from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent, depends, params }) => {
	depends('app:diagram');

	const { supabase, session } = await parent();
	const client = createApiClient(supabase, session?.access_token);
	const diagramService = createDiagramService(client);

	const [diagram, components] = await Promise.all([
		diagramService.get(params.id),
		diagramService.listComponents(),
	]);

	return { diagram, components };
};
