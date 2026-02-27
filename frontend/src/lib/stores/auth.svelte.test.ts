import { describe, it, expect } from 'vitest';
import { authStore } from './auth.svelte.js';

describe('AuthStore', () => {
	it('initializes with null values', () => {
		expect(authStore.session).toBeNull();
		expect(authStore.user).toBeNull();
		expect(authStore.profile).toBeNull();
	});

	it('sets session and user', () => {
		const mockSession = { access_token: 'test-token' } as any;
		const mockUser = { id: 'user-1', email: 'test@example.com' } as any;

		authStore.set(mockSession, mockUser);

		expect(authStore.session).toStrictEqual(mockSession);
		expect(authStore.user).toStrictEqual(mockUser);
	});

	it('clears all state', () => {
		authStore.set({ access_token: 'token' } as any, { id: 'user-1' } as any);
		authStore.setProfile({
			id: 'user-1',
			email: 'test@example.com',
			full_name: 'Test',
			avatar_url: null,
		});

		authStore.clear();

		expect(authStore.session).toBeNull();
		expect(authStore.user).toBeNull();
		expect(authStore.profile).toBeNull();
	});

	it('sets profile independently', () => {
		const profile = {
			id: 'user-1',
			email: 'test@example.com',
			full_name: 'Test User',
			avatar_url: null,
		};
		authStore.setProfile(profile);
		expect(authStore.profile).toStrictEqual(profile);
		authStore.clear();
	});
});
