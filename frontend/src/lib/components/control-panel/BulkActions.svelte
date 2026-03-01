<script lang="ts">
	import * as Select from '$lib/components/ui/select';
	import { Input } from '$lib/components/ui/input';
	import { Button } from '$lib/components/ui/button';
	import { Upload } from 'lucide-svelte';
	import { snakeToTitle } from '$lib/utils.js';
	import { ENTITY_TYPE_ORDER, OBJECT_STATUSES } from '$lib/stores/objects.svelte.js';
	import type { EntityType, ObjectStatus } from '$lib/types';

	let {
		filterEntityType = '',
		filterStatus = '',
		searchQuery = '',
		selectedCount = 0,
		totalCount = 0,
		pushableCount = 0,
		pushing = false,
		onfilterEntityType,
		onfilterStatus,
		onsearch,
		onapprove,
		onreject,
		onpush,
	}: {
		filterEntityType: EntityType | '';
		filterStatus: ObjectStatus | '';
		searchQuery: string;
		selectedCount: number;
		totalCount: number;
		pushableCount?: number;
		pushing?: boolean;
		onfilterEntityType: (value: EntityType | '') => void;
		onfilterStatus: (value: ObjectStatus | '') => void;
		onsearch: (value: string) => void;
		onapprove: () => void;
		onreject: () => void;
		onpush?: () => void;
	} = $props();
</script>

<div class="space-y-2 border-b px-4 py-3">
	<!-- Filters -->
	<div class="flex items-center gap-2">
		<Select.Root
			type="single"
			value={filterEntityType || undefined}
			onValueChange={(v) => onfilterEntityType(v === 'all' ? '' : ((v ?? '') as EntityType | ''))}
		>
			<Select.Trigger class="w-44">
				{filterEntityType ? snakeToTitle(filterEntityType) : 'All Types'}
			</Select.Trigger>
			<Select.Content>
				<Select.Item value="all">All Types</Select.Item>
				{#each ENTITY_TYPE_ORDER as et}
					<Select.Item value={et}>{snakeToTitle(et)}</Select.Item>
				{/each}
			</Select.Content>
		</Select.Root>

		<Select.Root
			type="single"
			value={filterStatus || undefined}
			onValueChange={(v) => onfilterStatus(v === 'all' ? '' : ((v ?? '') as ObjectStatus | ''))}
		>
			<Select.Trigger class="w-36">
				{filterStatus ? snakeToTitle(filterStatus) : 'All Statuses'}
			</Select.Trigger>
			<Select.Content>
				<Select.Item value="all">All Statuses</Select.Item>
				{#each OBJECT_STATUSES as s}
					<Select.Item value={s}>{snakeToTitle(s)}</Select.Item>
				{/each}
			</Select.Content>
		</Select.Root>

		<Input
			placeholder="Search..."
			value={searchQuery}
			oninput={(e) => onsearch(e.currentTarget.value)}
			class="max-w-xs"
		/>
	</div>

	<!-- Bulk actions -->
	<div class="flex items-center gap-2">
		<span class="text-muted-foreground text-sm">
			{selectedCount} selected of {totalCount}
		</span>
		<div class="flex-1"></div>
		<Button size="sm" variant="outline" disabled={selectedCount === 0} onclick={onapprove}>
			Approve Selected
		</Button>
		<Button size="sm" variant="outline" disabled={selectedCount === 0} onclick={onreject}>
			Reject Selected
		</Button>
		<Button
			size="sm"
			class="bg-green-600 text-white hover:bg-green-700"
			disabled={pushableCount === 0 || pushing}
			onclick={() => onpush?.()}
		>
			<Upload class="mr-1 size-3.5" />
			Push Selected ({pushableCount})
		</Button>
	</div>
</div>
