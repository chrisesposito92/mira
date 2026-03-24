<svelte:options namespace="svg" />

<script lang="ts">
	import { MONOGRAM_TEXT, SVG_FONT_FAMILY } from '../constants.js';

	let { initials, color, x, y, size }: {
		initials: string;
		color: string;
		x: number;
		y: number;
		size: number;
	} = $props();
</script>

<g>
	<circle
		cx={x + size / 2}
		cy={y + size / 2}
		r={size / 2}
		style="fill: {color};"
	/>
	<text
		x={x + size / 2}
		y={y + size / 2}
		text-anchor="middle"
		dominant-baseline="central"
		style="font-family: {SVG_FONT_FAMILY}; font-size: {size * 0.4}px; font-weight: 600; fill: {MONOGRAM_TEXT};"
	>
		{initials}
	</text>
</g>
