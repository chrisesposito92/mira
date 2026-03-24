import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import AddCustomSystemDialog from './AddCustomSystemDialog.svelte';

/**
 * Minimal mock of SupabaseClient for tests.
 * AddCustomSystemDialog only needs supabase to pass to createApiClient.
 */
function makeMockSupabase() {
	return {
		auth: {
			getSession: vi.fn().mockResolvedValue({
				data: { session: { access_token: 'test-token' } },
			}),
		},
	} as any;
}

describe('AddCustomSystemDialog', () => {
	it('shows dialog with title "Add Custom System" when open=true', () => {
		render(AddCustomSystemDialog, {
			props: {
				open: true,
				onsubmit: vi.fn(),
				supabase: makeMockSupabase(),
			},
		});
		// Dialog portals can create duplicate elements; check at least one exists
		const titles = screen.getAllByText('Add Custom System');
		expect(titles.length).toBeGreaterThanOrEqual(1);
	});

	it('has input with placeholder "e.g. Stripe" (name field)', () => {
		render(AddCustomSystemDialog, {
			props: {
				open: true,
				onsubmit: vi.fn(),
				supabase: makeMockSupabase(),
			},
		});
		// Dialog portal may duplicate DOM nodes; check at least one input exists
		const inputs = screen.getAllByPlaceholderText('e.g. Stripe');
		expect(inputs.length).toBeGreaterThanOrEqual(1);
	});

	it('has input with placeholder "e.g. stripe.com" (domain field)', () => {
		render(AddCustomSystemDialog, {
			props: {
				open: true,
				onsubmit: vi.fn(),
				supabase: makeMockSupabase(),
			},
		});
		const inputs = screen.getAllByPlaceholderText('e.g. stripe.com');
		expect(inputs.length).toBeGreaterThanOrEqual(1);
	});

	it('"Add System" button is present', () => {
		render(AddCustomSystemDialog, {
			props: {
				open: true,
				onsubmit: vi.fn(),
				supabase: makeMockSupabase(),
			},
		});
		const buttons = screen.getAllByText('Add System');
		expect(buttons.length).toBeGreaterThanOrEqual(1);
	});
});
