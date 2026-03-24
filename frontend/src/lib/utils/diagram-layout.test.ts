import { describe, it, expect } from "vitest";
import {
	layoutDiagram,
	parseMonogram,
	getConnectionMidpoint,
	estimatePillWidth,
	truncateSvgText,
	computeEdgeAnchor,
} from "./diagram-layout.js";
import {
	CANVAS_WIDTH,
	CANVAS_HEIGHT,
	HUB_CENTER_X,
	HUB_CENTER_Y,
	PROSPECT_Y,
	SYSTEM_CARD_WIDTH,
	SYSTEM_CARD_HEIGHT,
} from "$components/diagram/constants.js";
import type {
	DiagramContent,
	DiagramSystem,
	ComponentLibraryItem,
	LayoutResult,
} from "$types/diagram.js";

/** Helper: make a minimal DiagramContent. */
function makeContent(
	systems: DiagramSystem[] = [],
	connections: DiagramContent["connections"] = [],
): DiagramContent {
	return {
		systems,
		connections,
		settings: { background_color: "#1a1f36", show_labels: true },
	};
}

/** Helper: make a minimal system. */
function makeSys(
	overrides: Partial<DiagramSystem> & { id: string; name: string },
): DiagramSystem {
	return {
		component_library_id: null,
		logo_base64: null,
		x: 0,
		y: 0,
		category: null,
		...overrides,
	};
}

/** Helper: make a component library item. */
function makeLibItem(
	overrides: Partial<ComponentLibraryItem> & {
		id: string;
		name: string;
		category: string;
	},
): ComponentLibraryItem {
	return {
		slug: overrides.name.toLowerCase().replace(/\s/g, "-"),
		domain: "example.com",
		logo_base64: null,
		is_native_connector: false,
		display_order: 0,
		created_at: "2026-01-01T00:00:00Z",
		...overrides,
	};
}

describe("layoutDiagram", () => {
	it("Test 1: empty systems returns hub at center and prospect at top", () => {
		const content = makeContent();
		const result = layoutDiagram(content, []);

		expect(result.hub.x).toBe(HUB_CENTER_X);
		expect(result.hub.y).toBe(HUB_CENTER_Y);
		expect(result.prospect.x).toBe(HUB_CENTER_X);
		expect(result.prospect.y).toBe(PROSPECT_Y);
	});

	it("Test 2: single system in CRM category placed in first zone, not overlapping hub or prospect", () => {
		const sys = makeSys({
			id: "s1",
			name: "Salesforce",
			category: "CRM",
			component_library_id: "lib1",
		});
		const lib = makeLibItem({
			id: "lib1",
			name: "Salesforce",
			category: "CRM",
			display_order: 1,
		});
		const result = layoutDiagram(makeContent([sys]), [lib]);

		// Should not overlap hub
		const hubBounds = result.hub;
		const sysNode =
			result.standalone.find((s) => s.system.id === "s1") ||
			result.groups
				.flatMap((g) => g.systems)
				.find((s) => s.system.id === "s1");
		expect(sysNode).toBeDefined();

		// Check no overlap with hub center area
		const dx = Math.abs(sysNode!.x - hubBounds.x);
		const dy = Math.abs(sysNode!.y - hubBounds.y);
		expect(Math.sqrt(dx * dx + dy * dy)).toBeGreaterThan(100);

		// Check no overlap with prospect
		const prospectDy = Math.abs(sysNode!.y - result.prospect.y);
		expect(prospectDy).toBeGreaterThan(30);
	});

	it("Test 3: systems with same category are grouped into a PositionedGroup", () => {
		const systems = [
			makeSys({
				id: "s1",
				name: "Salesforce",
				category: "CRM",
				component_library_id: "lib1",
			}),
			makeSys({
				id: "s2",
				name: "HubSpot",
				category: "CRM",
				component_library_id: "lib2",
			}),
		];
		const lib = [
			makeLibItem({
				id: "lib1",
				name: "Salesforce",
				category: "CRM",
				display_order: 1,
			}),
			makeLibItem({
				id: "lib2",
				name: "HubSpot",
				category: "CRM",
				display_order: 1,
			}),
		];
		const result = layoutDiagram(makeContent(systems), lib);

		expect(result.groups.length).toBeGreaterThanOrEqual(1);
		const crmGroup = result.groups.find((g) => g.category === "CRM");
		expect(crmGroup).toBeDefined();
		expect(crmGroup!.systems.length).toBe(2);
	});

	it("Test 4: systems with null category and no role are placed as standalone", () => {
		const sys = makeSys({ id: "s1", name: "Custom Tool", category: null });
		const result = layoutDiagram(makeContent([sys]), []);

		// With no category and no role, could be detected as prospect fallback
		// or standalone. Let's add a prospect explicitly to avoid fallback.
		const systems = [
			makeSys({ id: "prospect", name: "My Platform", role: "prospect" }),
			makeSys({ id: "s1", name: "Custom Tool", category: null }),
		];
		const result2 = layoutDiagram(makeContent(systems), []);
		expect(result2.standalone.length).toBeGreaterThanOrEqual(1);
		expect(result2.standalone.some((s) => s.system.id === "s1")).toBe(true);
	});

	it("Test 5: multiple categories distribute across zones in order of display_order", () => {
		const systems = [
			makeSys({
				id: "s1",
				name: "Salesforce",
				category: "CRM",
				component_library_id: "lib1",
			}),
			makeSys({
				id: "s2",
				name: "Stripe",
				category: "Payments",
				component_library_id: "lib2",
			}),
			makeSys({
				id: "s3",
				name: "Snowflake",
				category: "Analytics",
				component_library_id: "lib3",
			}),
		];
		const lib = [
			makeLibItem({
				id: "lib1",
				name: "Salesforce",
				category: "CRM",
				display_order: 1,
			}),
			makeLibItem({
				id: "lib2",
				name: "Stripe",
				category: "Payments",
				display_order: 2,
			}),
			makeLibItem({
				id: "lib3",
				name: "Snowflake",
				category: "Analytics",
				display_order: 3,
			}),
		];
		const result = layoutDiagram(makeContent(systems), lib);

		// All three should appear either as standalone or groups
		const allSystems = [
			...result.standalone,
			...result.groups.flatMap((g) => g.systems),
		];
		expect(allSystems.length).toBe(3);

		// Each should have distinct x positions (different zones)
		const xPositions = allSystems.map((s) => s.x);
		const uniqueX = new Set(xPositions);
		expect(uniqueX.size).toBe(3);
	});

	it("Test 6: prospect identified by role === 'prospect' is positioned at top", () => {
		const systems = [
			makeSys({
				id: "p1",
				name: "Customer Platform",
				role: "prospect",
			}),
			makeSys({
				id: "s1",
				name: "Salesforce",
				category: "CRM",
				component_library_id: "lib1",
			}),
		];
		const lib = [
			makeLibItem({
				id: "lib1",
				name: "Salesforce",
				category: "CRM",
				display_order: 1,
			}),
		];
		const result = layoutDiagram(makeContent(systems), lib);

		expect(result.prospect.system.id).toBe("p1");
		expect(result.prospect.y).toBe(PROSPECT_Y);
		expect(result.prospect.x).toBe(HUB_CENTER_X);
	});

	it("Test 7: prospect fallback -- system with null component_library_id and null category", () => {
		const systems = [
			makeSys({
				id: "p1",
				name: "My Custom App",
				component_library_id: null,
				category: null,
			}),
			makeSys({
				id: "s1",
				name: "Stripe",
				category: "Payments",
				component_library_id: "lib1",
			}),
		];
		const lib = [
			makeLibItem({
				id: "lib1",
				name: "Stripe",
				category: "Payments",
				display_order: 1,
			}),
		];
		const result = layoutDiagram(makeContent(systems), lib);

		expect(result.prospect.system.id).toBe("p1");
		expect(result.prospect.y).toBe(PROSPECT_Y);
	});

	it("Test 8: all positioned nodes have x and y within canvas bounds", () => {
		const systems = Array.from({ length: 10 }, (_, i) =>
			makeSys({
				id: `s${i}`,
				name: `System ${i}`,
				category: `Cat${i % 3}`,
				component_library_id: `lib${i}`,
			}),
		);
		const lib = systems.map((s) =>
			makeLibItem({
				id: s.component_library_id!,
				name: s.name,
				category: s.category!,
				display_order: parseInt(s.category!.replace("Cat", "")),
			}),
		);
		const result = layoutDiagram(makeContent(systems), lib);

		const allNodes = [
			result.prospect,
			...result.standalone,
			...result.groups.flatMap((g) => g.systems),
		];
		for (const node of allNodes) {
			expect(node.x).toBeGreaterThanOrEqual(0);
			expect(node.x).toBeLessThanOrEqual(CANVAS_WIDTH);
			expect(node.y).toBeGreaterThanOrEqual(0);
			expect(node.y).toBeLessThanOrEqual(CANVAS_HEIGHT);
		}
	});

	it("Test 9: function is deterministic -- same input produces identical output", () => {
		const systems = [
			makeSys({
				id: "s1",
				name: "Salesforce",
				category: "CRM",
				component_library_id: "lib1",
			}),
			makeSys({
				id: "s2",
				name: "Stripe",
				category: "Payments",
				component_library_id: "lib2",
			}),
		];
		const lib = [
			makeLibItem({
				id: "lib1",
				name: "Salesforce",
				category: "CRM",
				display_order: 1,
			}),
			makeLibItem({
				id: "lib2",
				name: "Stripe",
				category: "Payments",
				display_order: 2,
			}),
		];
		const content = makeContent(systems);
		const result1 = layoutDiagram(content, lib);
		const result2 = layoutDiagram(content, lib);

		expect(result1).toEqual(result2);
	});

	it("Test 10: with many systems (15+), card sizes scale down proportionally", () => {
		const systems = Array.from({ length: 18 }, (_, i) =>
			makeSys({
				id: `s${i}`,
				name: `System ${i}`,
				category: `Cat${i % 5}`,
				component_library_id: `lib${i}`,
			}),
		);
		const lib = systems.map((s) =>
			makeLibItem({
				id: s.component_library_id!,
				name: s.name,
				category: s.category!,
				display_order: parseInt(s.category!.replace("Cat", "")),
			}),
		);
		const result = layoutDiagram(makeContent(systems), lib);

		// At least some nodes should have smaller dimensions than default
		const allNodes = [
			...result.standalone,
			...result.groups.flatMap((g) => g.systems),
		];
		const hasScaledDown = allNodes.some(
			(n) =>
				n.width < SYSTEM_CARD_WIDTH || n.height < SYSTEM_CARD_HEIGHT,
		);
		expect(hasScaledDown).toBe(true);
	});

	it("Test 17: nodePositions contains entries for hub and all system IDs", () => {
		const systems = [
			makeSys({ id: "p1", name: "Prospect", role: "prospect" }),
			makeSys({
				id: "s1",
				name: "Salesforce",
				category: "CRM",
				component_library_id: "lib1",
			}),
			makeSys({
				id: "s2",
				name: "Custom",
				category: null,
			}),
		];
		const lib = [
			makeLibItem({
				id: "lib1",
				name: "Salesforce",
				category: "CRM",
				display_order: 1,
			}),
		];
		const result = layoutDiagram(makeContent(systems), lib);

		expect(result.nodePositions["hub"]).toBeDefined();
		expect(result.nodePositions["p1"]).toBeDefined();
		expect(result.nodePositions["s1"]).toBeDefined();
		expect(result.nodePositions["s2"]).toBeDefined();
	});

	it("Test 18: group with 6+ systems has its zone center pushed further from hub", () => {
		// Create a group with 6 systems in same category
		const largeSystems = Array.from({ length: 6 }, (_, i) =>
			makeSys({
				id: `big${i}`,
				name: `System ${i}`,
				category: "BigGroup",
				component_library_id: `biglib${i}`,
			}),
		);
		// Create a group with 2 systems in different category
		const smallSystems = [
			makeSys({
				id: "sm1",
				name: "Small 1",
				category: "SmallGroup",
				component_library_id: "smlib1",
			}),
			makeSys({
				id: "sm2",
				name: "Small 2",
				category: "SmallGroup",
				component_library_id: "smlib2",
			}),
		];
		const allSystems = [...largeSystems, ...smallSystems];
		const lib = allSystems.map((s, i) =>
			makeLibItem({
				id: s.component_library_id!,
				name: s.name,
				category: s.category!,
				display_order: s.category === "BigGroup" ? 1 : 2,
			}),
		);

		const result = layoutDiagram(makeContent(allSystems), lib);

		const bigGroup = result.groups.find((g) => g.category === "BigGroup");
		const smallGroup = result.groups.find(
			(g) => g.category === "SmallGroup",
		);
		expect(bigGroup).toBeDefined();
		expect(smallGroup).toBeDefined();

		// Big group should be further from hub center than small group
		const bigDist = Math.sqrt(
			(bigGroup!.x + bigGroup!.width / 2 - HUB_CENTER_X) ** 2 +
				(bigGroup!.y + bigGroup!.height / 2 - HUB_CENTER_Y) ** 2,
		);
		const smallDist = Math.sqrt(
			(smallGroup!.x + smallGroup!.width / 2 - HUB_CENTER_X) ** 2 +
				(smallGroup!.y + smallGroup!.height / 2 - HUB_CENTER_Y) ** 2,
		);
		expect(bigDist).toBeGreaterThan(smallDist);
	});
});

describe("parseMonogram", () => {
	it("Test 11: returns initials and color for valid monogram format", () => {
		const result = parseMonogram("monogram:AB:#FF5722");
		expect(result).toEqual({ initials: "AB", color: "#FF5722" });
	});

	it("Test 12: returns null for non-monogram strings", () => {
		expect(parseMonogram(null)).toBeNull();
		expect(parseMonogram("")).toBeNull();
		expect(parseMonogram("data:image/png;base64,iVBOR...")).toBeNull();
		expect(parseMonogram("monogram:toolong:#FF5722")).toBeNull();
	});
});

describe("getConnectionMidpoint", () => {
	it("Test 13: returns midpoint of two coordinates", () => {
		const mid = getConnectionMidpoint(0, 0, 100, 200);
		expect(mid).toEqual({ x: 50, y: 100 });
	});
});

describe("estimatePillWidth", () => {
	it("Test 14: returns positive number proportional to text length", () => {
		const short = estimatePillWidth("API", 10);
		const long = estimatePillWidth("User Authentication Flow", 10);
		expect(short).toBeGreaterThan(0);
		expect(long).toBeGreaterThan(short);
	});
});

describe("truncateSvgText", () => {
	it("Test 15: truncates long text with ellipsis", () => {
		const result = truncateSvgText(
			"Enterprise Resource Planning Connector",
			16,
		);
		expect(result).toBe("Enterprise Resou...");
		expect(result.length).toBeLessThanOrEqual(19); // 16 chars + "..."
	});

	it("Test 16: returns short text unchanged", () => {
		expect(truncateSvgText("Short", 16)).toBe("Short");
	});
});

describe("computeEdgeAnchor", () => {
	it("Test 19: returns a point on the edge of a rect, not the center", () => {
		const rect = { x: 100, y: 100, width: 200, height: 100 };
		const centerX = rect.x + rect.width / 2;
		const centerY = rect.y + rect.height / 2;

		// Target is to the right
		const anchor = computeEdgeAnchor(rect, 500, 150);

		// Should not be the center
		expect(anchor.x !== centerX || anchor.y !== centerY).toBe(true);

		// Should be on or near the right edge
		expect(anchor.x).toBeCloseTo(300, 0); // right edge = x + width = 300

		// Target is directly above
		const anchorAbove = computeEdgeAnchor(rect, 200, 0);
		expect(anchorAbove.y).toBeCloseTo(100, 0); // top edge = y = 100
	});
});
