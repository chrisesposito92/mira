/**
 * Export pipeline for diagram PNG and SVG export.
 *
 * All SVG manipulation uses DOM APIs (DOMParser, cloneNode, setAttribute) --
 * never regex string surgery. The main entry point takes an explicit
 * SVGSVGElement parameter instead of querying the DOM internally.
 */

export type ExportFormat = "png" | "svg";

export interface ExportOptions {
	format: ExportFormat;
	customerName: string;
	title: string;
}

// ---------------------------------------------------------------------------
// Slugify & filename generation
// ---------------------------------------------------------------------------

export function slugify(text: string): string {
	return text
		.toLowerCase()
		.replace(/&/g, "")
		.replace(/[/\\:]/g, "")
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/-+/g, "-")
		.replace(/^-|-$/g, "");
}

export function generateFilename(
	customerName: string,
	title: string,
	format: ExportFormat,
): string {
	const base = customerName.trim() || title.trim() || "integration-diagram";
	return `${slugify(base)}.${format}`;
}

// ---------------------------------------------------------------------------
// ArrayBuffer → base64 (loop-based, not spread -- avoids stack overflow on 160KB+)
// ---------------------------------------------------------------------------

export function arrayBufferToBase64(buffer: ArrayBuffer): string {
	const bytes = new Uint8Array(buffer);
	let binary = "";
	for (let i = 0; i < bytes.byteLength; i++) {
		binary += String.fromCharCode(bytes[i]);
	}
	return btoa(binary);
}

// ---------------------------------------------------------------------------
// SVG → data URL (Unicode-safe)
// ---------------------------------------------------------------------------

export function svgToDataUrl(svgString: string): string {
	const bytes = new TextEncoder().encode(svgString);
	let binary = "";
	for (const byte of bytes) {
		binary += String.fromCharCode(byte);
	}
	const base64 = btoa(binary);
	return `data:image/svg+xml;base64,${base64}`;
}

// ---------------------------------------------------------------------------
// Font cache & warm function
// ---------------------------------------------------------------------------

let cachedFontBase64: string | null = null;

async function loadFontBase64(): Promise<string> {
	if (cachedFontBase64) return cachedFontBase64;
	const fontUrl = new URL("../assets/fonts/inter-latin-wght-normal.woff2", import.meta.url);
	const response = await fetch(fontUrl);
	if (!response.ok) throw new Error("Font fetch failed");
	const buffer = await response.arrayBuffer();
	cachedFontBase64 = arrayBufferToBase64(buffer);
	return cachedFontBase64;
}

/**
 * Pre-warm the font cache. Call on DiagramBuilder mount so first export
 * has zero font-loading latency. Safe to call multiple times -- no-ops
 * if already cached.
 */
export async function warmFontCache(): Promise<void> {
	try {
		await loadFontBase64();
	} catch {
		// Silently fail -- font will be lazy-loaded on first export as fallback
	}
}

// ---------------------------------------------------------------------------
// Validate image data URLs (EXPO-03 assertion)
// ---------------------------------------------------------------------------

export function validateImageDataUrls(svgDoc: Document): boolean {
	const images = svgDoc.querySelectorAll("image");
	for (const img of images) {
		const href =
			img.getAttribute("href") ||
			img.getAttributeNS("http://www.w3.org/1999/xlink", "href");
		if (href && !href.startsWith("data:")) {
			return false;
		}
	}
	return true;
}

// ---------------------------------------------------------------------------
// Font injection (DOM-based, not regex)
// ---------------------------------------------------------------------------

export function injectFont(svgDoc: Document, fontBase64: string): void {
	const styleEl = svgDoc.createElementNS("http://www.w3.org/2000/svg", "style");
	styleEl.textContent = `
		@font-face {
			font-family: 'Inter';
			font-style: normal;
			font-display: swap;
			font-weight: 100 900;
			src: url(data:font/woff2;base64,${fontBase64}) format('woff2');
		}
	`;
	const svgRoot = svgDoc.documentElement;
	svgRoot.insertBefore(styleEl, svgRoot.firstChild);
}

// ---------------------------------------------------------------------------
// Fix context-stroke markers (DOM-based, not regex)
// ---------------------------------------------------------------------------

export function fixContextStroke(svgDoc: Document): void {
	const defs = svgDoc.querySelector("defs");
	if (!defs) return;

	const lines = svgDoc.querySelectorAll("line");
	const uniqueColors = new Set<string>();
	for (const line of lines) {
		const stroke = line.getAttribute("stroke");
		if (stroke) uniqueColors.add(stroke);
	}

	if (uniqueColors.size === 0) return;

	const arrowheadMarker = defs.querySelector("#arrowhead");
	const sourceDotMarker = defs.querySelector("#source-dot");

	for (const color of uniqueColors) {
		const colorSuffix = color.replace("#", "");

		if (arrowheadMarker) {
			const cloned = arrowheadMarker.cloneNode(true) as Element;
			cloned.setAttribute("id", `arrowhead-${colorSuffix}`);
			const path = cloned.querySelector("path");
			if (path) path.setAttribute("fill", color);
			defs.appendChild(cloned);
		}

		if (sourceDotMarker) {
			const cloned = sourceDotMarker.cloneNode(true) as Element;
			cloned.setAttribute("id", `source-dot-${colorSuffix}`);
			const circle = cloned.querySelector("circle");
			if (circle) circle.setAttribute("fill", color);
			defs.appendChild(cloned);
		}
	}

	for (const line of lines) {
		const stroke = line.getAttribute("stroke");
		if (!stroke) continue;
		const colorSuffix = stroke.replace("#", "");

		const markerEnd = line.getAttribute("marker-end");
		if (markerEnd && markerEnd.includes("arrowhead")) {
			line.setAttribute("marker-end", `url(#arrowhead-${colorSuffix})`);
		}

		const markerStart = line.getAttribute("marker-start");
		if (markerStart && markerStart.includes("source-dot")) {
			line.setAttribute("marker-start", `url(#source-dot-${colorSuffix})`);
		}
	}
}

// ---------------------------------------------------------------------------
// Ensure SVG dimensions for standalone export
// ---------------------------------------------------------------------------

export function ensureSvgDimensions(svgDoc: Document): void {
	const svgRoot = svgDoc.documentElement;
	if (!svgRoot.hasAttribute("width")) {
		svgRoot.setAttribute("width", "1200");
	}
	if (!svgRoot.hasAttribute("height")) {
		svgRoot.setAttribute("height", "800");
	}
	// Remove percentage-based style (not meaningful in exported SVG)
	const style = svgRoot.getAttribute("style");
	if (style && style.includes("width: 100%")) {
		svgRoot.removeAttribute("style");
	}
}

// ---------------------------------------------------------------------------
// Download helpers
// ---------------------------------------------------------------------------

function triggerDownload(blob: Blob, filename: string): void {
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	URL.revokeObjectURL(url);
}

function downloadSvg(svgString: string, filename: string): void {
	const withDeclaration = '<?xml version="1.0" encoding="UTF-8"?>\n' + svgString;
	const blob = new Blob([withDeclaration], { type: "image/svg+xml;charset=utf-8" });
	triggerDownload(blob, filename);
}

async function downloadPng(svgString: string, filename: string): Promise<void> {
	const dataUrl = svgToDataUrl(svgString);

	const img = new Image();
	img.width = 1200;
	img.height = 800;

	const blob = await new Promise<Blob>((resolve, reject) => {
		img.onload = () => {
			const canvas = document.createElement("canvas");
			canvas.width = 2400;
			canvas.height = 1600;
			const ctx = canvas.getContext("2d");
			if (!ctx) {
				reject(new Error("Failed to get canvas context"));
				return;
			}
			ctx.drawImage(img, 0, 0, 2400, 1600);
			canvas.toBlob((b) => {
				if (b) resolve(b);
				else reject(new Error("Canvas toBlob returned null"));
			}, "image/png");
		};
		img.onerror = () => reject(new Error("Failed to load SVG as image"));
		img.src = dataUrl;
	});

	triggerDownload(blob, filename);
}

// ---------------------------------------------------------------------------
// Main export entry point
// ---------------------------------------------------------------------------

let exportInFlight = false;

export async function exportDiagram(
	svgEl: SVGSVGElement,
	options: ExportOptions,
): Promise<void> {
	if (exportInFlight) return;
	exportInFlight = true;
	try {
		// Clone SVG to Document via serialization + parse (DOM-based, not regex)
		const serialized = new XMLSerializer().serializeToString(svgEl);
		const parser = new DOMParser();
		const svgDoc = parser.parseFromString(serialized, "image/svg+xml");

		// Validate logo data URLs (EXPO-03 assertion)
		if (!validateImageDataUrls(svgDoc)) {
			console.warn("Some images are not base64 data URLs -- export may have missing logos");
		}

		// Ensure dimensions for standalone SVG
		ensureSvgDimensions(svgDoc);

		// Inject font (non-blocking -- font failure degrades gracefully)
		try {
			const fontBase64 = await loadFontBase64();
			injectFont(svgDoc, fontBase64);
		} catch {
			console.warn("Font injection failed, exporting without embedded font");
		}

		// Fix context-stroke markers
		fixContextStroke(svgDoc);

		// Serialize back to string
		const finalSvg = new XMLSerializer().serializeToString(svgDoc.documentElement);

		// Generate filename
		const filename = generateFilename(options.customerName, options.title, options.format);

		// Branch on format
		if (options.format === "svg") {
			downloadSvg(finalSvg, filename);
		} else {
			await downloadPng(finalSvg, filename);
		}
	} finally {
		exportInFlight = false;
	}
}
