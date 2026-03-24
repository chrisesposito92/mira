<script lang="ts">
	import type { DiagramContent, ComponentLibraryItem, LayoutResult } from "$types/diagram.js";
	import { layoutDiagram, computeEdgeAnchor, getConnectionMidpoint } from "$lib/utils/diagram-layout.js";
	import SvgDefs from "./SvgDefs.svelte";
	import HubNode from "./nodes/HubNode.svelte";
	import ProspectNode from "./nodes/ProspectNode.svelte";
	import GroupCard from "./nodes/GroupCard.svelte";
	import SystemCard from "./nodes/SystemCard.svelte";
	import ConnectionLine from "./connections/ConnectionLine.svelte";
	import ConnectionPill from "./connections/ConnectionPill.svelte";
	import { CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_BG, CONNECTION_COLORS } from "./constants.js";

	let {
		content,
		componentLibrary,
	}: {
		content: DiagramContent;
		componentLibrary: ComponentLibraryItem[];
	} = $props();

	const layout: LayoutResult = $derived(layoutDiagram(content, componentLibrary));
</script>

<svg
	viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}"
	xmlns="http://www.w3.org/2000/svg"
	style="width: 100%; height: auto;"
	role="img"
	aria-label="Integration architecture diagram"
>
	<SvgDefs />

	<!-- Layer 0: Background rect (NOT CSS background -- required for SVG export) -->
	<rect
		x="0"
		y="0"
		width={CANVAS_WIDTH}
		height={CANVAS_HEIGHT}
		style="fill: {CANVAS_BG};"
	/>

	<!-- Layer 1: Connection lines (bottom -- behind nodes) -->
	{#each content.connections as conn (conn.id)}
		<ConnectionLine
			connection={conn}
			nodePositions={layout.nodePositions}
			showLabels={false}
		/>
	{/each}

	<!-- Layer 2: Nodes (middle) -->
	<HubNode x={layout.hub.x} y={layout.hub.y} />

	<ProspectNode system={layout.prospect} />

	{#each layout.groups as group (group.category)}
		<GroupCard {group} />
	{/each}

	{#each layout.standalone as system (system.system.id)}
		<SystemCard positioned={system} />
	{/each}

	<!-- Layer 3: Connection pills (top -- above nodes, never hidden behind cards) -->
	{#if content.settings.show_labels}
		{#each content.connections as conn (conn.id)}
			{@const sourceRect = layout.nodePositions[conn.source_id]}
			{@const targetRect = layout.nodePositions[conn.target_id]}
			{#if sourceRect && targetRect && conn.label}
				{@const sCx = sourceRect.x + sourceRect.width / 2}
				{@const sCy = sourceRect.y + sourceRect.height / 2}
				{@const tCx = targetRect.x + targetRect.width / 2}
				{@const tCy = targetRect.y + targetRect.height / 2}
				{@const srcEdge = computeEdgeAnchor(sourceRect, tCx, tCy)}
				{@const tgtEdge = computeEdgeAnchor(targetRect, sCx, sCy)}
				{@const mid = getConnectionMidpoint(srcEdge.x, srcEdge.y, tgtEdge.x, tgtEdge.y)}
				{@const color = CONNECTION_COLORS[conn.connection_type] ?? CONNECTION_COLORS.api}
				<ConnectionPill x={mid.x} y={mid.y} label={conn.label} {color} />
			{/if}
		{/each}
	{/if}
</svg>
