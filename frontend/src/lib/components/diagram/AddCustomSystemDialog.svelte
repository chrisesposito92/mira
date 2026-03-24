<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import LogoPreview from './LogoPreview.svelte';
	import type { DiagramSystem } from '$lib/types';
	import { createApiClient } from '$lib/services';

	let {
		open = $bindable(false),
		onsubmit,
		supabase,
		accessToken,
	}: {
		open: boolean;
		onsubmit: (system: DiagramSystem) => void;
		supabase: import('@supabase/supabase-js').SupabaseClient;
		accessToken?: string;
	} = $props();

	let name = $state('');
	let domain = $state('');
	let logoBase64 = $state<string | null>(null);
	let logoLoading = $state(false);
	let logoError = $state<string | null>(null);

	/**
	 * Generate a deterministic hex color from a string.
	 */
	function hashColor(str: string): string {
		let hash = 0;
		for (let i = 0; i < str.length; i++) {
			hash = str.charCodeAt(i) + ((hash << 5) - hash);
		}
		const hue = Math.abs(hash) % 360;
		// Convert HSL to hex (saturated, medium lightness)
		const s = 0.65;
		const l = 0.45;
		const a = s * Math.min(l, 1 - l);
		const f = (n: number) => {
			const k = (n + hue / 30) % 12;
			const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
			return Math.round(255 * color)
				.toString(16)
				.padStart(2, '0');
		};
		return `#${f(0)}${f(8)}${f(4)}`;
	}

	/**
	 * Generate monogram format: monogram:<INITIALS>:<COLOR>
	 */
	function generateMonogram(systemName: string): string {
		const initials = systemName.trim().slice(0, 2).toUpperCase();
		const color = hashColor(systemName);
		return `monogram:${initials}:${color}`;
	}

	async function fetchLogo() {
		const trimmed = domain.trim();
		if (!trimmed) return;

		logoLoading = true;
		logoError = null;
		logoBase64 = null;

		try {
			const client = createApiClient(supabase, accessToken);
			const result = await client.get<{ logo_base64: string; domain: string }>(
				`/api/logos/proxy?domain=${encodeURIComponent(trimmed)}`,
			);
			logoBase64 = result.logo_base64;
		} catch {
			logoError = 'Could not fetch logo. A monogram will be used.';
			logoBase64 = null;
		} finally {
			logoLoading = false;
		}
	}

	function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		const trimmedName = name.trim();
		if (!trimmedName) return;

		const system: DiagramSystem = {
			id: crypto.randomUUID(),
			component_library_id: null,
			name: trimmedName,
			logo_base64: logoBase64 || generateMonogram(trimmedName),
			x: 0,
			y: 0,
			category: null,
			role: 'system',
		};

		onsubmit(system);
		reset();
	}

	function reset() {
		name = '';
		domain = '';
		logoBase64 = null;
		logoLoading = false;
		logoError = null;
	}
</script>

<Dialog.Root
	bind:open
	onOpenChange={(v) => {
		if (!v) reset();
	}}
>
	<Dialog.Content class="sm:max-w-md">
		<Dialog.Header>
			<Dialog.Title>Add Custom System</Dialog.Title>
			<Dialog.Description>Add a system to the architecture diagram.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleSubmit} class="space-y-4">
			<div class="space-y-2">
				<Label for="system-name">System name</Label>
				<Input id="system-name" bind:value={name} placeholder="e.g. Stripe" required />
			</div>
			<div class="space-y-2">
				<Label for="system-domain">Company domain</Label>
				<Input
					id="system-domain"
					bind:value={domain}
					placeholder="e.g. stripe.com"
					onblur={fetchLogo}
				/>
			</div>
			<LogoPreview {logoBase64} loading={logoLoading} error={logoError} />
			<Dialog.Footer>
				<Button variant="outline" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit" disabled={!name.trim()}>Add System</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
