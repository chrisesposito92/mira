<svelte:options namespace="svg" />

<script lang="ts">
	// Shared SVG defs: shadow filter, arrowhead marker, source dot marker.
	// All values are inline constants -- no external imports needed.
</script>

<defs>
	<!-- Card drop shadow filter -->
	<filter id="card-shadow" x="-10%" y="-10%" width="120%" height="130%">
		<feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="rgba(0,0,0,0.15)" flood-opacity="1" />
	</filter>

	<!-- Arrowhead marker (inherits line color via context-stroke) -->
	<marker id="arrowhead" viewBox="0 0 10 10" refX="10" refY="5"
		markerWidth="8" markerHeight="8" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
		<path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
	</marker>

	<!-- Source dot marker (inherits line color via context-stroke) -->
	<marker id="source-dot" viewBox="0 0 10 10" refX="5" refY="5"
		markerWidth="8" markerHeight="8" markerUnits="userSpaceOnUse">
		<circle cx="5" cy="5" r="4" fill="context-stroke" />
	</marker>
</defs>
