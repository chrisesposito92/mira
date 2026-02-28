import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient, ApiError } from './api.js';

function mockSupabase(token = 'test-token') {
	return {
		auth: {
			getSession: vi.fn().mockResolvedValue({
				data: { session: { access_token: token } },
			}),
		},
	} as any;
}

describe('ApiClient', () => {
	let client: ApiClient;

	beforeEach(() => {
		client = new ApiClient('http://localhost:8000', mockSupabase());
		vi.restoreAllMocks();
	});

	it('GET sends auth header', async () => {
		const spy = vi
			.spyOn(globalThis, 'fetch')
			.mockResolvedValue(new Response(JSON.stringify({ id: '1' }), { status: 200 }));

		await client.get('/api/projects');

		expect(spy).toHaveBeenCalledOnce();
		const [url, init] = spy.mock.calls[0];
		expect(url).toBe('http://localhost:8000/api/projects');
		expect((init?.headers as Record<string, string>)['Authorization']).toBe('Bearer test-token');
	});

	it('POST sends JSON body', async () => {
		const spy = vi
			.spyOn(globalThis, 'fetch')
			.mockResolvedValue(new Response(JSON.stringify({ id: '1', name: 'Test' }), { status: 201 }));

		await client.post('/api/projects', { name: 'Test' });

		const [, init] = spy.mock.calls[0];
		expect(init?.method).toBe('POST');
		expect(init?.body).toBe(JSON.stringify({ name: 'Test' }));
		expect((init?.headers as Record<string, string>)['Content-Type']).toBe('application/json');
	});

	it('PATCH sends correct method', async () => {
		vi.spyOn(globalThis, 'fetch').mockResolvedValue(
			new Response(JSON.stringify({ id: '1' }), { status: 200 }),
		);

		await client.patch('/api/projects/1', { name: 'Updated' });

		const [, init] = vi.mocked(fetch).mock.calls[0];
		expect(init?.method).toBe('PATCH');
	});

	it('DELETE returns void for 204', async () => {
		vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));

		const result = await client.delete('/api/projects/1');
		expect(result).toBeUndefined();
	});

	it('throws ApiError on non-ok response', async () => {
		vi.spyOn(globalThis, 'fetch').mockResolvedValue(
			new Response(JSON.stringify({ detail: 'Not found' }), {
				status: 404,
				statusText: 'Not Found',
			}),
		);

		try {
			await client.get('/api/projects/bad');
			expect.unreachable('Should have thrown');
		} catch (e) {
			expect(e).toBeInstanceOf(ApiError);
			expect((e as ApiError).status).toBe(404);
			expect((e as ApiError).detail).toBe('Not found');
		}
	});

	it('upload sends FormData without Content-Type', async () => {
		const spy = vi
			.spyOn(globalThis, 'fetch')
			.mockResolvedValue(
				new Response(JSON.stringify({ id: '1', filename: 'test.pdf' }), { status: 201 }),
			);

		const formData = new FormData();
		formData.append('file', new Blob(['content']), 'test.pdf');
		await client.upload('/api/projects/1/documents', formData);

		const [, init] = spy.mock.calls[0];
		expect(init?.method).toBe('POST');
		expect(init?.body).toBe(formData);
		// Should NOT have Content-Type (browser sets multipart boundary)
		expect((init?.headers as Record<string, string>)['Content-Type']).toBeUndefined();
	});
});
