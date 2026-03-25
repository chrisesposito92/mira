<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Pencil, Trash2 } from 'lucide-svelte';
	import type { DiagramConnection } from '$lib/types';

	let {
		connection,
		systemName,
		onedit,
		ondelete,
	}: {
		connection: DiagramConnection;
		systemName: (id: string) => string;
		onedit: () => void;
		ondelete: () => void;
	} = $props();

	const TYPE_COLORS: Record<DiagramConnection['connection_type'], string> = {
		native_connector: '#00C853',
		webhook_api: '#2196F3',
		custom_build: '#FF9800',
		api: '#90A4AE',
	};

	const TYPE_NAMES: Record<DiagramConnection['connection_type'], string> = {
		native_connector: 'Native Connector',
		webhook_api: 'Webhook / API',
		custom_build: 'Custom Build',
		api: 'API',
	};

	const arrow = connection.direction === 'bidirectional' ? '<->' : '->';
</script>

<div class="flex items-center justify-between gap-2 rounded-md border px-3 py-2">
	<div class="min-w-0 flex-1">
		<p class="truncate text-sm">
			{systemName(connection.source_id)} {arrow}
			{systemName(connection.target_id)}
		</p>
		{#if connection.label}
			<p class="text-muted-foreground truncate text-xs">{connection.label}</p>
		{/if}
	</div>
	<Badge
		class="shrink-0 text-xs"
		style="background-color: {TYPE_COLORS[connection.connection_type]}; color: white;"
	>
		{TYPE_NAMES[connection.connection_type]}
	</Badge>
	<div class="flex shrink-0 gap-0.5">
		<Button variant="ghost" size="sm" class="size-7 p-0" onclick={onedit}>
			<Pencil class="size-3.5" />
		</Button>
		<Button
			variant="ghost"
			size="sm"
			class="hover:text-destructive size-7 p-0"
			aria-label="Delete connection to {systemName(connection.target_id)}"
			onclick={ondelete}
		>
			<Trash2 class="size-3.5" />
		</Button>
	</div>
</div>
