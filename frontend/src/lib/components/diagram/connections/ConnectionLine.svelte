<svelte:options namespace="svg" />

<script lang="ts">
	import type { DiagramConnection, NodePositionMap } from "$types/diagram.js";
	import {
		CONNECTION_COLORS,
		CONNECTION_STROKE_WIDTH,
		CONNECTION_DASH,
	} from "../constants.js";
	import { computeEdgeAnchor, getConnectionMidpoint } from "$lib/utils/diagram-layout.js";
	import ConnectionPill from "./ConnectionPill.svelte";

	let {
		connection,
		nodePositions,
		showLabels,
	}: {
		connection: DiagramConnection;
		nodePositions: NodePositionMap;
		showLabels: boolean;
	} = $props();

	// Look up source and target bounding boxes
	const sourceRect = $derived(nodePositions[connection.source_id]);
	const targetRect = $derived(nodePositions[connection.target_id]);

	// Compute centers
	const sCx = $derived(sourceRect ? sourceRect.x + sourceRect.width / 2 : 0);
	const sCy = $derived(sourceRect ? sourceRect.y + sourceRect.height / 2 : 0);
	const tCx = $derived(targetRect ? targetRect.x + targetRect.width / 2 : 0);
	const tCy = $derived(targetRect ? targetRect.y + targetRect.height / 2 : 0);

	// Edge-anchored endpoints (not center-to-center)
	const sourceAnchor = $derived(
		sourceRect ? computeEdgeAnchor(sourceRect, tCx, tCy) : null,
	);
	const targetAnchor = $derived(
		targetRect ? computeEdgeAnchor(targetRect, sCx, sCy) : null,
	);

	// Color from connection type with fallback
	const color = $derived(
		CONNECTION_COLORS[connection.connection_type] ?? CONNECTION_COLORS.api,
	);

	// Midpoint for pill placement
	const midpoint = $derived(
		sourceAnchor && targetAnchor
			? getConnectionMidpoint(sourceAnchor.x, sourceAnchor.y, targetAnchor.x, targetAnchor.y)
			: null,
	);

	// Marker references
	const markerStart = $derived(
		connection.direction === "bidirectional" ? "url(#arrowhead)" : "url(#source-dot)",
	);
	const markerEnd = "url(#arrowhead)";
</script>

{#if sourceRect && targetRect && sourceAnchor && targetAnchor}
	<g>
		<line
			x1={sourceAnchor.x}
			y1={sourceAnchor.y}
			x2={targetAnchor.x}
			y2={targetAnchor.y}
			marker-start={markerStart}
			marker-end={markerEnd}
			style="stroke: {color}; stroke-width: {CONNECTION_STROKE_WIDTH}; stroke-dasharray: {CONNECTION_DASH};"
		/>
		{#if showLabels && connection.label && midpoint}
			<ConnectionPill
				x={midpoint.x}
				y={midpoint.y}
				label={connection.label}
				{color}
			/>
		{/if}
	</g>
{/if}
