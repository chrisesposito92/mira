import type { Session, User } from '@supabase/supabase-js';
import type { UserProfile } from '$lib/types/auth.js';

class AuthStore {
	session = $state<Session | null>(null);
	user = $state<User | null>(null);
	profile = $state<UserProfile | null>(null);

	isAuthenticated = $derived(!!this.session);

	displayName = $derived(
		this.profile?.full_name || this.user?.user_metadata?.full_name || this.user?.email || ''
	);

	userInitials = $derived.by(() => {
		const name = this.displayName;
		if (!name) return '?';
		const parts = name.split(' ').filter(Boolean);
		if (parts.length >= 2) {
			return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
		}
		return name.slice(0, 2).toUpperCase();
	});

	set(session: Session | null, user: User | null) {
		this.session = session;
		this.user = user;
	}

	setProfile(profile: UserProfile | null) {
		this.profile = profile;
	}

	clear() {
		this.session = null;
		this.user = null;
		this.profile = null;
	}
}

export const authStore = new AuthStore();
