<script lang="ts">
	import { page } from '$app/state';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb';

	const labelMap: Record<string, string> = {
		dashboard: 'Dashboard',
		projects: 'Projects',
		orgs: 'Org Connections',
		'use-cases': 'Use Cases',
		'control-panel': 'Control Panel',
		settings: 'Settings'
	};

	const crumbs = $derived.by(() => {
		const segments = page.url.pathname.split('/').filter(Boolean);
		let href = '';
		return segments.map((segment) => {
			href += `/${segment}`;
			return {
				label: labelMap[segment] || decodeURIComponent(segment),
				href
			};
		});
	});
</script>

<Breadcrumb.Root>
	<Breadcrumb.List>
		{#each crumbs as crumb, i}
			{#if i > 0}
				<Breadcrumb.Separator />
			{/if}
			<Breadcrumb.Item>
				{#if i === crumbs.length - 1}
					<Breadcrumb.Page>{crumb.label}</Breadcrumb.Page>
				{:else}
					<Breadcrumb.Link href={crumb.href}>{crumb.label}</Breadcrumb.Link>
				{/if}
			</Breadcrumb.Item>
		{/each}
	</Breadcrumb.List>
</Breadcrumb.Root>
