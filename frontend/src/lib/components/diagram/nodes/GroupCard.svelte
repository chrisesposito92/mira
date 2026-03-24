<svelte:options namespace="svg" />

<script lang="ts">
	import {
		CARD_BG,
		CARD_BORDER,
		CARD_BORDER_RADIUS,
		GROUP_CARD_PADDING,
		GROUP_CARD_GAP,
		LOGO_SIZE,
		LOGO_GRID_COLS,
		TEXT_SECONDARY,
		SVG_FONT_FAMILY,
		MAX_CATEGORY_NAME_CHARS,
	} from '../constants.js';
	import { truncateSvgText } from '$lib/utils/diagram-layout.js';
	import GroupItem from './GroupItem.svelte';
	import type { PositionedGroup } from '$lib/types';

	let {
		group,
	}: {
		group: PositionedGroup;
	} = $props();

	const truncatedCategory = $derived(truncateSvgText(group.category, MAX_CATEGORY_NAME_CHARS));
</script>

<g>
	<!-- Group card background -->
	<rect
		x={group.x}
		y={group.y}
		width={group.width}
		height={group.height}
		rx={CARD_BORDER_RADIUS}
		filter="url(#card-shadow)"
		style="fill: {CARD_BG}; stroke: {CARD_BORDER}; stroke-width: 1;"
	/>

	<!-- Category header -->
	<text
		x={group.x + GROUP_CARD_PADDING}
		y={group.y + GROUP_CARD_PADDING + 12}
		style="font-family: {SVG_FONT_FAMILY}; font-size: 12px; font-weight: 600; fill: {TEXT_SECONDARY};"
	>
		{truncatedCategory}
	</text>

	<!-- Compact logo grid using GroupItem (NOT SystemCard) -->
	{#each group.systems as sys, i}
		<GroupItem
			system={sys.system}
			x={group.x + GROUP_CARD_PADDING + (i % LOGO_GRID_COLS) * (LOGO_SIZE + GROUP_CARD_GAP)}
			y={group.y +
				GROUP_CARD_PADDING +
				24 +
				Math.floor(i / LOGO_GRID_COLS) * (LOGO_SIZE + GROUP_CARD_GAP + 14)}
		/>
	{/each}
</g>
