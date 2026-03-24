/**
 * Hub-and-spoke layout algorithm for integration architecture diagrams.
 *
 * Pure function with no DOM or Svelte dependencies. Computes positions for
 * all diagram nodes based on category zones, scaling, and BBox buffering.
 */

import type {
	DiagramContent,
	DiagramSystem,
	ComponentLibraryItem,
	PositionedSystem,
	PositionedGroup,
	LayoutResult,
	NodePositionMap,
} from "$types/diagram.js";

import {
	CANVAS_WIDTH,
	CANVAS_HEIGHT,
	CANVAS_PADDING,
	HUB_RADIUS,
	HUB_CENTER_X,
	HUB_CENTER_Y,
	PROSPECT_Y,
	SYSTEM_CARD_WIDTH,
	SYSTEM_CARD_HEIGHT,
	GROUP_CARD_PADDING,
	GROUP_CARD_GAP,
	LOGO_SIZE,
	LOGO_GRID_COLS,
} from "$components/diagram/constants.js";

// ─── Monogram parsing ─────────────────────────────────────────────

const MONOGRAM_RE = /^monogram:([A-Z]{1,3}):(#[0-9A-Fa-f]{6})$/;

/**
 * Parse a monogram-encoded logo_base64 string.
 * Returns `{initials, color}` for valid `monogram:AB:#FF5722` format, or null.
 */
export function parseMonogram(
	logo_base64: string | null,
): { initials: string; color: string } | null {
	if (!logo_base64) return null;
	const match = MONOGRAM_RE.exec(logo_base64);
	if (!match) return null;
	return { initials: match[1], color: match[2] };
}

// ─── Text helpers ─────────────────────────────────────────────────

/**
 * Truncate text for SVG rendering. If the text exceeds maxChars,
 * it is clipped and "..." is appended.
 */
export function truncateSvgText(text: string, maxChars: number): string {
	if (text.length <= maxChars) return text;
	return text.slice(0, maxChars) + "...";
}

/**
 * Estimate the rendered width of a pill label in SVG.
 * Uses an average character width multiplier.
 */
export function estimatePillWidth(text: string, fontSize: number): number {
	const avgCharWidth = fontSize * 0.6;
	return text.length * avgCharWidth + 20; // 20 = pill horizontal padding
}

// ─── Connection helpers ───────────────────────────────────────────

/**
 * Get the midpoint between two coordinates.
 */
export function getConnectionMidpoint(
	x1: number,
	y1: number,
	x2: number,
	y2: number,
): { x: number; y: number } {
	return { x: (x1 + x2) / 2, y: (y1 + y2) / 2 };
}

/**
 * Compute the anchor point on a rectangle edge where a line from the rect
 * center to a target point intersects the rect boundary.
 *
 * Uses parametric line-rect intersection.
 */
export function computeEdgeAnchor(
	rect: { x: number; y: number; width: number; height: number },
	targetX: number,
	targetY: number,
): { x: number; y: number } {
	const cx = rect.x + rect.width / 2;
	const cy = rect.y + rect.height / 2;
	const dx = targetX - cx;
	const dy = targetY - cy;

	// If target is at center, return center (degenerate case)
	if (dx === 0 && dy === 0) {
		return { x: cx, y: cy };
	}

	const halfW = rect.width / 2;
	const halfH = rect.height / 2;

	// Find the smallest positive t where the line crosses a rect boundary.
	// Line: P(t) = center + t * (target - center)
	// We need t in (0, 1] where the line exits the rect.
	let t = Infinity;

	if (dx !== 0) {
		const tRight = halfW / Math.abs(dx);
		if (tRight > 0 && tRight < t) t = tRight;
	}
	if (dy !== 0) {
		const tBottom = halfH / Math.abs(dy);
		if (tBottom > 0 && tBottom < t) t = tBottom;
	}

	// Fallback if t is still Infinity (shouldn't happen in practice)
	if (!isFinite(t)) t = 1;

	return {
		x: cx + dx * t,
		y: cy + dy * t,
	};
}

// ─── Layout algorithm ─────────────────────────────────────────────

/** Zone angles in radians -- 5 zones distributed clockwise from left. */
const ZONE_ANGLES = [
	Math.PI, // left
	Math.PI * 0.7, // bottom-left
	Math.PI * 0.5, // bottom
	Math.PI * 0.3, // bottom-right
	0, // right
];

const BASE_RADIAL_DISTANCE = 250;
const BBOX_BUFFER_PER_EXTRA = 15;
const BBOX_BUFFER_THRESHOLD = 4;
const SCALE_THRESHOLD = 15;

/**
 * Identify the prospect system from the diagram content.
 *
 * Priority:
 * 1. Explicit `role === 'prospect'`
 * 2. Fallback: `component_library_id === null && category === null` (first match)
 * 3. Final fallback: synthetic prospect
 */
function identifyProspect(systems: DiagramSystem[]): {
	prospect: DiagramSystem;
	remaining: DiagramSystem[];
} {
	// Priority 1: explicit role
	const byRole = systems.find((s) => s.role === "prospect");
	if (byRole) {
		return {
			prospect: byRole,
			remaining: systems.filter((s) => s.id !== byRole.id),
		};
	}

	// Priority 2: heuristic fallback
	const heuristic = systems.find(
		(s) => s.component_library_id === null && s.category === null,
	);
	if (heuristic) {
		return {
			prospect: heuristic,
			remaining: systems.filter((s) => s.id !== heuristic.id),
		};
	}

	// Priority 3: synthetic prospect
	const synthetic: DiagramSystem = {
		id: "__prospect__",
		component_library_id: null,
		name: "Your Product/Platform",
		logo_base64: null,
		x: 0,
		y: 0,
		category: null,
		role: "prospect",
	};
	return { prospect: synthetic, remaining: systems };
}

/**
 * Group systems by category, ordered by component library display_order.
 */
function groupByCategory(
	systems: DiagramSystem[],
	library: ComponentLibraryItem[],
): {
	categorized: Map<string, DiagramSystem[]>;
	uncategorized: DiagramSystem[];
} {
	const libMap = new Map<string, ComponentLibraryItem>();
	for (const item of library) {
		libMap.set(item.id, item);
	}

	const categorized = new Map<string, DiagramSystem[]>();
	const uncategorized: DiagramSystem[] = [];

	for (const sys of systems) {
		if (sys.category) {
			const existing = categorized.get(sys.category) || [];
			existing.push(sys);
			categorized.set(sys.category, existing);
		} else {
			uncategorized.push(sys);
		}
	}

	// Sort categories by display_order of their first member's library item
	const categoryOrder = new Map<string, number>();
	for (const [category, members] of categorized) {
		let minOrder = Infinity;
		for (const sys of members) {
			if (sys.component_library_id) {
				const libItem = libMap.get(sys.component_library_id);
				if (libItem && libItem.display_order < minOrder) {
					minOrder = libItem.display_order;
				}
			}
		}
		categoryOrder.set(category, isFinite(minOrder) ? minOrder : 999);
	}

	// Re-build the map in sorted order
	const sortedEntries = [...categorized.entries()].sort(
		(a, b) =>
			(categoryOrder.get(a[0]) ?? 999) -
			(categoryOrder.get(b[0]) ?? 999),
	);
	const sortedMap = new Map<string, DiagramSystem[]>(sortedEntries);

	return { categorized: sortedMap, uncategorized };
}

/**
 * Compute a scale factor when the system count exceeds the threshold.
 */
function computeScaleFactor(totalSystems: number): number {
	if (totalSystems <= SCALE_THRESHOLD) return 1;
	return Math.sqrt(SCALE_THRESHOLD / totalSystems);
}

/**
 * Compute group card dimensions based on number of systems.
 */
function computeGroupDimensions(
	systemCount: number,
	scale: number,
): { width: number; height: number } {
	const scaledLogoSize = LOGO_SIZE * scale;
	const cols = Math.min(systemCount, LOGO_GRID_COLS);
	const rows = Math.ceil(systemCount / LOGO_GRID_COLS);

	const width =
		cols * scaledLogoSize +
		(cols - 1) * GROUP_CARD_GAP +
		GROUP_CARD_PADDING * 2;
	const headerHeight = 20 * scale; // category header
	const height =
		headerHeight +
		rows * (scaledLogoSize + GROUP_CARD_GAP) -
		GROUP_CARD_GAP +
		GROUP_CARD_PADDING * 2;

	return { width, height };
}

/**
 * Clamp a value within bounds.
 */
function clamp(value: number, min: number, max: number): number {
	return Math.max(min, Math.min(max, value));
}

/** Zone item for layout placement. */
interface ZoneItem {
	type: "group" | "standalone";
	category?: string;
	systems: DiagramSystem[];
}

/**
 * Main layout function. Pure, deterministic, no side effects.
 *
 * Computes hub-and-spoke positions for all diagram systems.
 * Categories are assigned to 5 zones in clockwise order by display_order.
 * Groups with 2+ systems are rendered as group cards. Single systems are standalone.
 * BBox buffering pushes large groups further from hub to prevent overlap.
 * Scale factor reduces card sizes when total system count exceeds 15.
 */
export function layoutDiagram(
	content: DiagramContent,
	componentLibrary: ComponentLibraryItem[],
): LayoutResult {
	const { prospect, remaining } = identifyProspect(content.systems);
	const totalSystems = remaining.length;
	const scale = computeScaleFactor(totalSystems);

	const scaledCardWidth = SYSTEM_CARD_WIDTH * scale;
	const scaledCardHeight = SYSTEM_CARD_HEIGHT * scale;

	// Hub position (always center)
	const hubWidth = HUB_RADIUS * 2;
	const hubHeight = HUB_RADIUS * 2;
	const hub = {
		x: HUB_CENTER_X,
		y: HUB_CENTER_Y,
		width: hubWidth,
		height: hubHeight,
	};

	// Prospect position (always top-center)
	const prospectPositioned: PositionedSystem = {
		system: prospect,
		x: HUB_CENTER_X,
		y: PROSPECT_Y,
		width: scaledCardWidth,
		height: scaledCardHeight,
	};

	// Group remaining systems by category
	const { categorized, uncategorized } = groupByCategory(
		remaining,
		componentLibrary,
	);

	const groups: PositionedGroup[] = [];
	const standalone: PositionedSystem[] = [];
	const nodePositions: NodePositionMap = {};

	// Register hub in nodePositions
	nodePositions["hub"] = {
		x: HUB_CENTER_X - hubWidth / 2,
		y: HUB_CENTER_Y - hubHeight / 2,
		width: hubWidth,
		height: hubHeight,
	};

	// Register prospect
	nodePositions[prospect.id] = {
		x: HUB_CENTER_X - scaledCardWidth / 2,
		y: PROSPECT_Y - scaledCardHeight / 2,
		width: scaledCardWidth,
		height: scaledCardHeight,
	};

	// Collect all items to place in zones
	const zoneItems: ZoneItem[] = [];

	for (const [category, systems] of categorized) {
		if (systems.length >= 2) {
			zoneItems.push({ type: "group", category, systems });
		} else {
			zoneItems.push({ type: "standalone", systems });
		}
	}

	for (const sys of uncategorized) {
		zoneItems.push({ type: "standalone", systems: [sys] });
	}

	// Assign items to zones
	for (let i = 0; i < zoneItems.length; i++) {
		const item = zoneItems[i];
		const zoneAngle = ZONE_ANGLES[i % ZONE_ANGLES.length];

		if (item.type === "group" && item.category) {
			const systemCount = item.systems.length;
			const dims = computeGroupDimensions(systemCount, scale);

			// BBox buffering: push further from hub for large groups
			let radialDist = BASE_RADIAL_DISTANCE;
			if (systemCount > BBOX_BUFFER_THRESHOLD) {
				radialDist +=
					(systemCount - BBOX_BUFFER_THRESHOLD) *
					BBOX_BUFFER_PER_EXTRA;
			}

			const centerX =
				HUB_CENTER_X + Math.cos(zoneAngle) * radialDist;
			const centerY =
				HUB_CENTER_Y + Math.sin(zoneAngle) * radialDist;

			// Clamp group to canvas bounds
			const groupX = clamp(
				centerX - dims.width / 2,
				CANVAS_PADDING,
				CANVAS_WIDTH - CANVAS_PADDING - dims.width,
			);
			const groupY = clamp(
				centerY - dims.height / 2,
				CANVAS_PADDING,
				CANVAS_HEIGHT - CANVAS_PADDING - dims.height,
			);

			const positionedSystems: PositionedSystem[] = [];
			const scaledLogoSize = LOGO_SIZE * scale;

			for (let j = 0; j < item.systems.length; j++) {
				const sys = item.systems[j];
				const col = j % LOGO_GRID_COLS;
				const row = Math.floor(j / LOGO_GRID_COLS);
				const headerHeight = 20 * scale;

				const sysX =
					groupX +
					GROUP_CARD_PADDING +
					col * (scaledLogoSize + GROUP_CARD_GAP);
				const sysY =
					groupY +
					GROUP_CARD_PADDING +
					headerHeight +
					row * (scaledLogoSize + GROUP_CARD_GAP);

				const ps: PositionedSystem = {
					system: sys,
					x: sysX,
					y: sysY,
					width: scaledLogoSize,
					height: scaledLogoSize,
				};
				positionedSystems.push(ps);

				nodePositions[sys.id] = {
					x: sysX,
					y: sysY,
					width: scaledLogoSize,
					height: scaledLogoSize,
				};
			}

			groups.push({
				category: item.category,
				systems: positionedSystems,
				x: groupX,
				y: groupY,
				width: dims.width,
				height: dims.height,
			});
		} else {
			// Standalone system
			const sys = item.systems[0];
			const radialDist = BASE_RADIAL_DISTANCE;
			const centerX =
				HUB_CENTER_X + Math.cos(zoneAngle) * radialDist;
			const centerY =
				HUB_CENTER_Y + Math.sin(zoneAngle) * radialDist;

			const cardX = clamp(
				centerX - scaledCardWidth / 2,
				CANVAS_PADDING,
				CANVAS_WIDTH - CANVAS_PADDING - scaledCardWidth,
			);
			const cardY = clamp(
				centerY - scaledCardHeight / 2,
				CANVAS_PADDING,
				CANVAS_HEIGHT - CANVAS_PADDING - scaledCardHeight,
			);

			const ps: PositionedSystem = {
				system: sys,
				x: cardX,
				y: cardY,
				width: scaledCardWidth,
				height: scaledCardHeight,
			};
			standalone.push(ps);

			nodePositions[sys.id] = {
				x: cardX,
				y: cardY,
				width: scaledCardWidth,
				height: scaledCardHeight,
			};
		}
	}

	return {
		hub,
		prospect: prospectPositioned,
		groups,
		standalone,
		nodePositions,
	};
}
