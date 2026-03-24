<svelte:options namespace="svg" />

<script lang="ts">
	import {
		PILL_PADDING_Y,
		PILL_BORDER_RADIUS,
		PILL_TEXT,
		SVG_FONT_FAMILY,
		MAX_PILL_LABEL_CHARS,
	} from '../constants.js';
	import { estimatePillWidth, truncateSvgText } from '$lib/utils/diagram-layout.js';

	let {
		x,
		y,
		label,
		color,
	}: {
		x: number;
		y: number;
		label: string;
		color: string;
	} = $props();

	const fontSize = 10;
	const truncatedLabel = $derived(truncateSvgText(label, MAX_PILL_LABEL_CHARS));
	const pillWidth = $derived(estimatePillWidth(truncatedLabel, fontSize));
	const pillHeight = $derived(fontSize + PILL_PADDING_Y * 2);
</script>

<g>
	<rect
		x={x - pillWidth / 2}
		y={y - pillHeight / 2}
		width={pillWidth}
		height={pillHeight}
		rx={PILL_BORDER_RADIUS}
		style="fill: {color};"
	/>
	<text
		{x}
		{y}
		text-anchor="middle"
		dominant-baseline="central"
		style="font-family: {SVG_FONT_FAMILY}; font-size: {fontSize}px; font-weight: 500; fill: {PILL_TEXT};"
	>
		{truncatedLabel}
	</text>
</g>
