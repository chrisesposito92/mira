<script lang="ts">
	import { page } from '$app/state';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb';

	const labelMap: Record<string, string> = {
		dashboard: 'Dashboard',
		projects: 'Projects',
		orgs: 'Org Connections',
		'use-cases': 'Use Cases',
		'control-panel': 'Control Panel',
		settings: 'Settings',
	};

	const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

	function segmentLabel(segment: string, prevSegment?: string): string {
		if (uuidPattern.test(segment)) {
			// Map parent route to a readable label
			const parentLabels: Record<string, string> = { projects: 'Project', orgs: 'Connection' };
			return prevSegment ? (parentLabels[prevSegment] ?? 'Detail') : 'Detail';
		}
		return labelMap[segment] || decodeURIComponent(segment);
	}

	const crumbs = $derived.by(() => {
		const segments = page.url.pathname.split('/').filter(Boolean);
		let href = '';
		return segments.map((segment, i) => {
			href += `/${segment}`;
			return {
				label: segmentLabel(segment, segments[i - 1]),
				href,
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
