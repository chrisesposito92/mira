<svelte:options namespace="svg" />

<script lang="ts">
	import {
		CARD_BG,
		CARD_BORDER,
		CARD_BORDER_RADIUS,
		TEXT_PRIMARY,
		SVG_FONT_FAMILY,
		LOGO_SIZE,
		MAX_SYSTEM_NAME_CHARS,
	} from '../constants.js';
	import { parseMonogram, truncateSvgText } from '$lib/utils/diagram-layout.js';
	import MonogramSvg from './MonogramSvg.svelte';
	import type { PositionedSystem } from '$lib/types';

	let {
		positioned,
	}: {
		positioned: PositionedSystem;
	} = $props();

	const monogram = $derived(parseMonogram(positioned.system.logo_base64));
	const isBase64Image = $derived(
		positioned.system.logo_base64 !== null &&
			!positioned.system.logo_base64.startsWith('monogram:'),
	);
	const truncatedName = $derived(truncateSvgText(positioned.system.name, MAX_SYSTEM_NAME_CHARS));

	// Logo positioning: centered horizontally in card, offset from top
	const logoX = $derived(positioned.x + (positioned.width - LOGO_SIZE) / 2);
	const logoY = $derived(positioned.y + 12);
</script>

<g>
	<!-- Card background -->
	<rect
		x={positioned.x}
		y={positioned.y}
		width={positioned.width}
		height={positioned.height}
		rx={CARD_BORDER_RADIUS}
		filter="url(#card-shadow)"
		style="fill: {CARD_BG}; stroke: {CARD_BORDER}; stroke-width: 1;"
	/>

	<!-- Logo area -->
	{#if monogram}
		<MonogramSvg
			initials={monogram.initials}
			color={monogram.color}
			x={logoX}
			y={logoY}
			size={LOGO_SIZE}
		/>
	{:else if isBase64Image}
		<image
			href={positioned.system.logo_base64}
			x={logoX}
			y={logoY}
			width={LOGO_SIZE}
			height={LOGO_SIZE}
			preserveAspectRatio="xMidYMid meet"
		/>
	{:else}
		<!-- No logo fallback: gray circle -->
		<circle
			cx={logoX + LOGO_SIZE / 2}
			cy={logoY + LOGO_SIZE / 2}
			r={LOGO_SIZE / 2}
			style="fill: #E2E8F0;"
		/>
	{/if}

	<!-- System name -->
	<text
		x={positioned.x + positioned.width / 2}
		y={positioned.y + positioned.height - 12}
		text-anchor="middle"
		dominant-baseline="central"
		style="font-family: {SVG_FONT_FAMILY}; font-size: 11px; font-weight: 500; fill: {TEXT_PRIMARY};"
	>
		{truncatedName}
	</text>
</g>
