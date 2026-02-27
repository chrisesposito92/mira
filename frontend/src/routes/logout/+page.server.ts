import { redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	redirect(303, '/login');
};

export const actions: Actions = {
	default: async ({ locals: { supabase } }) => {
		await supabase.auth.signOut();
		redirect(303, '/login');
	}
};
