<svelte:options namespace="svg" />

<script lang="ts">
	import {
		CARD_BG,
		CARD_BORDER,
		CARD_BORDER_RADIUS,
		GROUP_CARD_PADDING,
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

	<!-- Compact logo grid using GroupItem — uses pre-computed layout coords -->
	{#each group.systems as sys}
		<GroupItem system={sys.system} x={sys.x} y={sys.y} />
	{/each}
</g>
