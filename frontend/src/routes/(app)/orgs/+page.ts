import { createApiClient, createOrgConnectionService } from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent, depends }) => {
	depends('app:connections');

	const { supabase, session } = await parent();
	const client = createApiClient(supabase, session?.access_token);
	const service = createOrgConnectionService(client);

	try {
		const connections = await service.list();
		return { connections };
	} catch {
		return { connections: [] };
	}
};
