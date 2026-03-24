import { describe, it, expect } from "vitest";
import { render } from "@testing-library/svelte";
import GroupCard from "./GroupCard.svelte";
import type { PositionedGroup } from "$lib/types";

const baseGroup: PositionedGroup = {
	category: "Finance Stack",
	systems: [
		{
			system: {
				id: "sys-1",
				component_library_id: "cl-1",
				name: "Stripe",
				logo_base64: null,
				x: 0,
				y: 0,
				category: "Finance Stack",
			},
			x: 56,
			y: 52,
			width: 36,
			height: 36,
		},
		{
			system: {
				id: "sys-2",
				component_library_id: "cl-2",
				name: "QuickBooks",
				logo_base64: "monogram:QB:#4CAF50",
				x: 0,
				y: 0,
				category: "Finance Stack",
			},
			x: 104,
			y: 52,
			width: 36,
			height: 36,
		},
	],
	x: 40,
	y: 200,
	width: 150,
	height: 120,
};

describe("GroupCard", () => {
	it("renders category name header text", () => {
		const { container } = render(GroupCard, {
			props: { group: baseGroup },
		});
		const allText = container.textContent || "";
		expect(allText).toContain("Finance Stack");
	});

	it("renders system names for each system in the group (via GroupItem)", () => {
		const { container } = render(GroupCard, {
			props: { group: baseGroup },
		});
		const allText = container.textContent || "";
		expect(allText).toContain("Stripe");
		expect(allText).toContain("QuickBooks");
	});

	it("has a containing rect with fill #FFFFFF (CARD_BG)", () => {
		const { container } = render(GroupCard, {
			props: { group: baseGroup },
		});
		const rects = container.querySelectorAll("rect");
		const bgRect = Array.from(rects).find((r) => {
			const style = r.getAttribute("style") || "";
			return style.includes("#FFFFFF");
		});
		expect(bgRect).toBeTruthy();
	});

	it("does NOT render nested SystemCard components (review MEDIUM-HIGH concern)", () => {
		const { container } = render(GroupCard, {
			props: { group: baseGroup },
		});
		// SystemCard would add filter="url(#card-shadow)" on nested rects.
		// GroupCard should have exactly 1 rect (the group container), not nested card rects.
		const rects = container.querySelectorAll("rect");
		// Count rects with card-shadow filter -- should be exactly 1 (the group card itself)
		const shadowRects = Array.from(rects).filter((r) => {
			const filter = r.getAttribute("filter") || "";
			return filter.includes("card-shadow");
		});
		expect(shadowRects.length).toBe(1);
	});

	it("renders MonogramSvg for systems with monogram logo_base64", () => {
		const { container } = render(GroupCard, {
			props: { group: baseGroup },
		});
		// QuickBooks has monogram:QB:#4CAF50, so we should see "QB" text
		const allText = container.textContent || "";
		expect(allText).toContain("QB");
	});
});
