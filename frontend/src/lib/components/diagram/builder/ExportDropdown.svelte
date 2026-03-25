<script lang="ts">
	import { exportDiagram } from '$lib/utils/export-diagram.js';
	import type { ExportFormat } from '$lib/utils/export-diagram.js';
	import { Button } from '$lib/components/ui/button';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import { Download, Image, FileCode } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';

	let {
		disabled = false,
		customerName = '',
		title = '',
	}: {
		disabled: boolean;
		customerName: string;
		title: string;
	} = $props();

	let exporting = $state(false);

	async function handleExport(format: ExportFormat) {
		if (exporting) return;
		exporting = true;
		try {
			const svgEl = document.querySelector('svg[role="img"]') as SVGSVGElement | null;
			if (!svgEl) {
				toast.error('Export failed. Try refreshing the page and exporting again.');
				return;
			}
			await exportDiagram(svgEl, { format, customerName, title });
		} catch {
			toast.error('Export failed. Try refreshing the page and exporting again.');
		} finally {
			exporting = false;
		}
	}
</script>

{#if disabled}
	<Tooltip.Provider>
		<Tooltip.Root>
			<Tooltip.Trigger>
				{#snippet child({ props })}
					<span class="inline-flex" {...props}>
						<Button variant="outline" size="sm" disabled>
							<Download class="mr-2 size-4" />
							Export
						</Button>
					</span>
				{/snippet}
			</Tooltip.Trigger>
			<Tooltip.Content>
				<p>Add at least one system to export</p>
			</Tooltip.Content>
		</Tooltip.Root>
	</Tooltip.Provider>
{:else}
	<DropdownMenu.Root>
		<DropdownMenu.Trigger>
			{#snippet child({ props })}
				<Button variant="outline" size="sm" {...props}>
					<Download class="mr-2 size-4" />
					Export
				</Button>
			{/snippet}
		</DropdownMenu.Trigger>
		<DropdownMenu.Content align="end">
			<DropdownMenu.Item onclick={() => handleExport('png')}>
				<Image class="mr-2 size-4" />
				PNG
			</DropdownMenu.Item>
			<DropdownMenu.Item onclick={() => handleExport('svg')}>
				<FileCode class="mr-2 size-4" />
				SVG
			</DropdownMenu.Item>
		</DropdownMenu.Content>
	</DropdownMenu.Root>
{/if}
