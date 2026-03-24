<svelte:options namespace="svg" />

<script lang="ts">
	import {
		HUB_RADIUS,
		HUB_BG,
		HUB_ACCENT_BORDER,
		HUB_ACCENT_BORDER_WIDTH,
		CARD_BORDER_RADIUS,
		TEXT_PRIMARY,
		TEXT_SECONDARY,
		SVG_FONT_FAMILY,
		HUB_CAPABILITIES,
	} from '../constants.js';

	let { x, y }: {
		x: number;
		y: number;
	} = $props();
</script>

<g>
	<!-- Hub background with green accent border -->
	<rect
		x={x - HUB_RADIUS}
		y={y - HUB_RADIUS}
		width={HUB_RADIUS * 2}
		height={HUB_RADIUS * 2}
		rx={CARD_BORDER_RADIUS}
		filter="url(#card-shadow)"
		style="fill: {HUB_BG}; stroke: {HUB_ACCENT_BORDER}; stroke-width: {HUB_ACCENT_BORDER_WIDTH};"
	/>

	<!-- Hub title -->
	<text
		x={x}
		y={y - 50}
		text-anchor="middle"
		dominant-baseline="central"
		style="font-family: {SVG_FONT_FAMILY}; font-size: 18px; font-weight: 700; fill: {TEXT_PRIMARY};"
	>
		m3ter
	</text>

	<!-- Capability labels: 2 columns x 3 rows -->
	{#each HUB_CAPABILITIES as cap, i}
		<text
			x={x + (i % 2 === 0 ? -35 : 35)}
			y={y - 20 + Math.floor(i / 2) * 16}
			text-anchor="middle"
			dominant-baseline="central"
			style="font-family: {SVG_FONT_FAMILY}; font-size: 10px; font-weight: 500; fill: {TEXT_SECONDARY};"
		>
			{cap}
		</text>
	{/each}
</g>
