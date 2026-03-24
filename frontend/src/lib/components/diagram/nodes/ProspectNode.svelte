<svelte:options namespace="svg" />

<script lang="ts">
	import {
		PROSPECT_BG,
		PROSPECT_BORDER,
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
		system,
	}: {
		system: PositionedSystem;
	} = $props();

	const monogram = $derived(parseMonogram(system.system.logo_base64));
	const isBase64Image = $derived(
		system.system.logo_base64 !== null && !system.system.logo_base64.startsWith('monogram:'),
	);
	const truncatedName = $derived(truncateSvgText(system.system.name, MAX_SYSTEM_NAME_CHARS));

	// Logo positioning: centered horizontally in card, offset from top
	const logoX = $derived(system.x + (system.width - LOGO_SIZE) / 2);
	const logoY = $derived(system.y + 12);
</script>

<g>
	<!-- Card background with prospect border -->
	<rect
		x={system.x}
		y={system.y}
		width={system.width}
		height={system.height}
		rx={CARD_BORDER_RADIUS}
		filter="url(#card-shadow)"
		style="fill: {PROSPECT_BG}; stroke: {PROSPECT_BORDER}; stroke-width: 1;"
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
			href={system.system.logo_base64}
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
		x={system.x + system.width / 2}
		y={system.y + system.height - 16}
		text-anchor="middle"
		dominant-baseline="central"
		style="font-family: {SVG_FONT_FAMILY}; font-size: 14px; font-weight: 600; fill: {TEXT_PRIMARY};"
	>
		{truncatedName}
	</text>
</g>
