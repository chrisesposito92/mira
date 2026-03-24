<svelte:options namespace="svg" />

<script lang="ts">
	import { LOGO_SIZE, TEXT_PRIMARY, SVG_FONT_FAMILY, MAX_SYSTEM_NAME_CHARS } from '../constants.js';
	import { parseMonogram, truncateSvgText } from '$lib/utils/diagram-layout.js';
	import MonogramSvg from './MonogramSvg.svelte';
	import type { DiagramSystem } from '$lib/types';

	let {
		system,
		x,
		y,
	}: {
		system: DiagramSystem;
		x: number;
		y: number;
	} = $props();

	const monogram = $derived(parseMonogram(system.logo_base64));
	const isBase64Image = $derived(
		system.logo_base64 !== null && !system.logo_base64.startsWith('monogram:'),
	);
	const truncatedName = $derived(truncateSvgText(system.name, MAX_SYSTEM_NAME_CHARS));
</script>

<g>
	{#if monogram}
		<MonogramSvg initials={monogram.initials} color={monogram.color} {x} {y} size={LOGO_SIZE} />
	{:else if isBase64Image}
		<image
			href={system.logo_base64}
			{x}
			{y}
			width={LOGO_SIZE}
			height={LOGO_SIZE}
			preserveAspectRatio="xMidYMid meet"
		/>
	{:else}
		<!-- No logo fallback: gray circle placeholder -->
		<circle
			cx={x + LOGO_SIZE / 2}
			cy={y + LOGO_SIZE / 2}
			r={LOGO_SIZE / 2}
			style="fill: #E2E8F0;"
		/>
	{/if}
	<text
		x={x + LOGO_SIZE / 2}
		y={y + LOGO_SIZE + 12}
		text-anchor="middle"
		style="font-family: {SVG_FONT_FAMILY}; font-size: 9px; font-weight: 500; fill: {TEXT_PRIMARY};"
	>
		{truncatedName}
	</text>
</g>
