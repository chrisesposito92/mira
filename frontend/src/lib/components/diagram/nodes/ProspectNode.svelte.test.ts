import { describe, it, expect } from "vitest";
import { render } from "@testing-library/svelte";
import ProspectNode from "./ProspectNode.svelte";
import type { PositionedSystem } from "$lib/types";

const baseSystem: PositionedSystem = {
	system: {
		id: "prospect-1",
		component_library_id: null,
		name: "Your Product/Platform",
		logo_base64: null,
		x: 0,
		y: 0,
		category: null,
		role: "prospect",
	},
	x: 540,
	y: 10,
	width: 120,
	height: 100,
};

describe("ProspectNode", () => {
	it("renders the system name text", () => {
		const { container } = render(ProspectNode, {
			props: { system: baseSystem },
		});
		const allText = container.textContent || "";
		// "Your Product/Platform" (21 chars) truncated at 16 = "Your Product/Pla..."
		expect(allText).toContain("Your Product/Pla...");
	});

	it("has a rect with prospect border stroke #94A3B8", () => {
		const { container } = render(ProspectNode, {
			props: { system: baseSystem },
		});
		const rects = container.querySelectorAll("rect");
		// jsdom normalizes hex #94A3B8 to rgb(148, 163, 184) in inline styles
		const prospectRect = Array.from(rects).find((r) => {
			const style = r.getAttribute("style") || "";
			return style.includes("#94A3B8") || style.includes("rgb(148, 163, 184)");
		});
		expect(prospectRect).toBeTruthy();
	});

	it("does NOT contain any class= attributes on SVG elements (REND-03)", () => {
		const { container } = render(ProspectNode, {
			props: { system: baseSystem },
		});
		const allElements = container.querySelectorAll("rect, text, g, circle, path, line, image");
		for (const el of allElements) {
			expect(el.hasAttribute("class")).toBe(false);
		}
	});
});
