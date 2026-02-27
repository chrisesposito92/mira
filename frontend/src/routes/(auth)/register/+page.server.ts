import { redirect, fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals: { safeGetSession } }) => {
	const { session } = await safeGetSession();
	if (session) {
		redirect(303, '/dashboard');
	}
};

export const actions: Actions = {
	default: async ({ request, locals: { supabase } }) => {
		const formData = await request.formData();
		const fullName = formData.get('full_name') as string;
		const email = formData.get('email') as string;
		const password = formData.get('password') as string;
		const confirmPassword = formData.get('confirm_password') as string;

		if (!fullName || !email || !password) {
			return fail(400, { error: 'All fields are required', email, fullName });
		}

		if (password !== confirmPassword) {
			return fail(400, { error: 'Passwords do not match', email, fullName });
		}

		if (password.length < 6) {
			return fail(400, { error: 'Password must be at least 6 characters', email, fullName });
		}

		const { data: signUpData, error } = await supabase.auth.signUp({
			email,
			password,
			options: {
				data: { full_name: fullName },
			},
		});

		if (error) {
			return fail(400, { error: error.message, email, fullName });
		}

		// If auto-confirm is enabled, session exists — go to dashboard.
		// If email confirmation is required, session is null — show confirmation message.
		if (signUpData.session) {
			redirect(303, '/dashboard');
		}

		return { success: true, email };
	},
};
