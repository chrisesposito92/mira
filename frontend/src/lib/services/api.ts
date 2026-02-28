import type { SupabaseClient } from '@supabase/supabase-js';

export class ApiError extends Error {
	constructor(
		public status: number,
		public detail: string,
	) {
		super(detail);
		this.name = 'ApiError';
	}
}

export class ApiClient {
	constructor(
		private baseUrl: string,
		private supabase: SupabaseClient,
		private accessToken?: string,
	) {}

	private async headers(): Promise<Record<string, string>> {
		const headers: Record<string, string> = {};
		let token = this.accessToken;
		if (!token) {
			// Browser-only fallback — getSession() is safe in the browser.
			// Server-side callers must pass a pre-validated accessToken instead
			// (see AGENTS.md: never use getSession() alone on the server).
			const {
				data: { session },
			} = await this.supabase.auth.getSession();
			token = session?.access_token;
		}
		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}
		return headers;
	}

	private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
		const authHeaders = await this.headers();
		const res = await fetch(`${this.baseUrl}${path}`, {
			...init,
			headers: {
				'Content-Type': 'application/json',
				...authHeaders,
				...(init.headers as Record<string, string>),
			},
		});

		if (!res.ok) {
			let detail = res.statusText;
			try {
				const body = await res.json();
				detail = body.detail ?? JSON.stringify(body);
			} catch {
				// use statusText
			}
			throw new ApiError(res.status, detail);
		}

		if (res.status === 204) return undefined as T;
		return res.json();
	}

	async get<T>(path: string): Promise<T> {
		return this.request<T>(path);
	}

	async post<T>(path: string, data: unknown): Promise<T> {
		return this.request<T>(path, {
			method: 'POST',
			body: JSON.stringify(data),
		});
	}

	async patch<T>(path: string, data: unknown): Promise<T> {
		return this.request<T>(path, {
			method: 'PATCH',
			body: JSON.stringify(data),
		});
	}

	async delete(path: string): Promise<void> {
		return this.request<void>(path, { method: 'DELETE' });
	}

	async upload<T>(path: string, formData: FormData): Promise<T> {
		const authHeaders = await this.headers();
		const res = await fetch(`${this.baseUrl}${path}`, {
			method: 'POST',
			headers: authHeaders,
			body: formData,
		});

		if (!res.ok) {
			let detail = res.statusText;
			try {
				const body = await res.json();
				detail = body.detail ?? JSON.stringify(body);
			} catch {
				// use statusText
			}
			throw new ApiError(res.status, detail);
		}

		return res.json();
	}
}

export function createApiClient(supabase: SupabaseClient, accessToken?: string): ApiClient {
	// Uses import.meta.env for testability — $env/static/public is unavailable in vitest.
	// Use || (not ??) so empty string also falls back to default.
	const baseUrl = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';
	return new ApiClient(baseUrl, supabase, accessToken);
}
