import { createApiClient, createOrgConnectionService } from '$lib/services';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent }) => {
	const { supabase } = await parent();
	const client = createApiClient(supabase);
	const service = createOrgConnectionService(client);
	const connections = await service.list();

	return { connections, supabase };
};
