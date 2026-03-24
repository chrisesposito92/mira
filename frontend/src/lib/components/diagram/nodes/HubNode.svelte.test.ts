import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/svelte";
import HubNode from "./HubNode.svelte";

/**
 * Tests for HubNode SVG component.
 *
 * HubNode renders the m3ter hub node with green accent border,
 * title text, and 6 capability labels. All styling is inline (no class=).
 *
 * Note: SVG-namespace components are rendered inside a host <svg> by the
 * component itself (or we test markup via container queries).
 */
describe("HubNode", () => {
	it("renders m3ter title text", () => {
		const { container } = render(HubNode, { props: { x: 600, y: 400 } });
		const texts = container.querySelectorAll("text");
		const titleText = Array.from(texts).find((t) =>
			t.textContent?.includes("m3ter"),
		);
		expect(titleText).toBeTruthy();
	});

	it("renders all 6 capability labels", () => {
		const { container } = render(HubNode, { props: { x: 600, y: 400 } });
		const capabilities = ["Usage", "Pricing", "Rating", "Credits", "Alerts", "Limits"];
		const allText = container.textContent || "";
		for (const cap of capabilities) {
			expect(allText).toContain(cap);
		}
	});

	it("has a rect with green accent border stroke #00C853", () => {
		const { container } = render(HubNode, { props: { x: 600, y: 400 } });
		const rects = container.querySelectorAll("rect");
		const hubRect = Array.from(rects).find((r) => {
			const style = r.getAttribute("style") || "";
			return style.includes("#00C853");
		});
		expect(hubRect).toBeTruthy();
	});

	it("does NOT contain any class= attributes on SVG elements (REND-03)", () => {
		const { container } = render(HubNode, { props: { x: 600, y: 400 } });
		// Check all SVG elements (rect, text, g, circle, etc.)
		const allElements = container.querySelectorAll("rect, text, g, circle, path, line");
		for (const el of allElements) {
			expect(el.hasAttribute("class")).toBe(false);
		}
	});
});
