import { describe, it, expect } from "vitest";
import { render } from "@testing-library/svelte";
import ConnectionLine from "./ConnectionLine.svelte";
import type { DiagramConnection, NodePositionMap } from "$types/diagram.js";

/** Helper: make a minimal connection. */
function makeConnection(
	overrides: Partial<DiagramConnection> = {},
): DiagramConnection {
	return {
		id: "conn-1",
		source_id: "sys-a",
		target_id: "sys-b",
		label: "Events",
		direction: "unidirectional",
		connection_type: "native_connector",
		...overrides,
	};
}

/** Standard node positions for two systems -- not overlapping. */
const mockPositions: NodePositionMap = {
	"sys-a": { x: 100, y: 100, width: 120, height: 100 },
	"sys-b": { x: 500, y: 300, width: 120, height: 100 },
};

/**
 * Wrapper to render ConnectionLine inside an SVG host element.
 * SVG namespace components must be rendered inside <svg>.
 */
function renderInSvg(
	props: {
		connection: DiagramConnection;
		nodePositions: NodePositionMap;
		showLabels: boolean;
	},
) {
	const { container } = render(ConnectionLine, { props });
	// The component renders SVG elements; wrap in an SVG for query purposes
	return container;
}

describe("ConnectionLine", () => {
	it("renders a <line> element with stroke-dasharray 6,4", () => {
		const container = renderInSvg({
			connection: makeConnection(),
			nodePositions: mockPositions,
			showLabels: true,
		});
		const line = container.querySelector("line");
		expect(line).not.toBeNull();
		const style = line!.getAttribute("style") || "";
		expect(style).toContain("stroke-dasharray: 6,4");
	});

	it("uses CONNECTION_COLORS[connection_type] -- native_connector renders #00C853", () => {
		const container = renderInSvg({
			connection: makeConnection({ connection_type: "native_connector" }),
			nodePositions: mockPositions,
			showLabels: true,
		});
		const line = container.querySelector("line");
		const style = line!.getAttribute("style") || "";
		expect(style).toContain("#00C853");
	});

	it("webhook_api connection renders with stroke #2196F3", () => {
		const container = renderInSvg({
			connection: makeConnection({ connection_type: "webhook_api" }),
			nodePositions: mockPositions,
			showLabels: true,
		});
		const line = container.querySelector("line");
		const style = line!.getAttribute("style") || "";
		expect(style).toContain("#2196F3");
	});

	it("custom_build connection renders with stroke #FF9800", () => {
		const container = renderInSvg({
			connection: makeConnection({ connection_type: "custom_build" }),
			nodePositions: mockPositions,
			showLabels: true,
		});
		const line = container.querySelector("line");
		const style = line!.getAttribute("style") || "";
		expect(style).toContain("#FF9800");
	});

	it("unidirectional connection has marker-start source-dot and marker-end arrowhead", () => {
		const container = renderInSvg({
			connection: makeConnection({ direction: "unidirectional" }),
			nodePositions: mockPositions,
			showLabels: true,
		});
		const line = container.querySelector("line");
		expect(line!.getAttribute("marker-start")).toBe("url(#source-dot)");
		expect(line!.getAttribute("marker-end")).toBe("url(#arrowhead)");
	});

	it("bidirectional connection has marker-start and marker-end both as arrowhead", () => {
		const container = renderInSvg({
			connection: makeConnection({ direction: "bidirectional" }),
			nodePositions: mockPositions,
			showLabels: true,
		});
		const line = container.querySelector("line");
		expect(line!.getAttribute("marker-start")).toBe("url(#arrowhead)");
		expect(line!.getAttribute("marker-end")).toBe("url(#arrowhead)");
	});

	it("renders a ConnectionPill with the label text when showLabels is true", () => {
		const container = renderInSvg({
			connection: makeConnection({ label: "User Events" }),
			nodePositions: mockPositions,
			showLabels: true,
		});
		// Pill renders a <text> element with the label
		const texts = container.querySelectorAll("text");
		const labelText = Array.from(texts).find((t) =>
			t.textContent?.includes("User Events"),
		);
		expect(labelText).toBeDefined();
	});

	it("does NOT render ConnectionPill when showLabels is false", () => {
		const container = renderInSvg({
			connection: makeConnection({ label: "User Events" }),
			nodePositions: mockPositions,
			showLabels: false,
		});
		// No text elements should exist (pill text is the only text in ConnectionLine)
		const texts = container.querySelectorAll("text");
		expect(texts.length).toBe(0);
	});

	it("does NOT contain any class= attributes on SVG elements", () => {
		const container = renderInSvg({
			connection: makeConnection(),
			nodePositions: mockPositions,
			showLabels: true,
		});
		const allElements = container.querySelectorAll("line, rect, text, g, circle");
		for (const el of allElements) {
			expect(el.getAttribute("class")).toBeNull();
		}
	});

	it("gracefully handles missing node positions (skips rendering)", () => {
		const container = renderInSvg({
			connection: makeConnection({ source_id: "missing-a", target_id: "missing-b" }),
			nodePositions: mockPositions,
			showLabels: true,
		});
		const line = container.querySelector("line");
		expect(line).toBeNull();
	});

	it("line coordinates use edge anchors, not center coordinates", () => {
		const container = renderInSvg({
			connection: makeConnection(),
			nodePositions: mockPositions,
			showLabels: true,
		});
		const line = container.querySelector("line");
		expect(line).not.toBeNull();

		// Source center would be 160, 150 (x + width/2, y + height/2)
		// Edge anchor should differ from center
		const x1 = parseFloat(line!.getAttribute("x1") || "0");
		const y1 = parseFloat(line!.getAttribute("y1") || "0");

		// The source center is at (160, 150). Edge anchor should be on the
		// rectangle boundary, so at least one coordinate must differ from center.
		const sourceCenterX = 100 + 120 / 2; // 160
		const sourceCenterY = 100 + 100 / 2; // 150

		// Edge anchor point should NOT equal the center point
		const isAtCenter = x1 === sourceCenterX && y1 === sourceCenterY;
		expect(isAtCenter).toBe(false);
	});
});
