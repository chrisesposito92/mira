import { describe, it, expect } from 'vitest';
import {
	slugify,
	generateFilename,
	arrayBufferToBase64,
	injectFont,
	fixContextStroke,
	ensureSvgDimensions,
	svgToDataUrl,
	validateImageDataUrls,
} from './export-diagram.js';

// Uses inline style for stroke (matches real ConnectionLine.svelte output)
const SAMPLE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" role="img"><defs><marker id="arrowhead" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker><marker id="source-dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="8" markerHeight="8" markerUnits="userSpaceOnUse"><circle cx="5" cy="5" r="4" fill="context-stroke"/></marker></defs><rect x="0" y="0" width="1200" height="800" style="fill: #1a1f36;"/><line x1="100" y1="200" x2="300" y2="400" style="stroke: #00C853; stroke-width: 2; stroke-dasharray: 6,4;" marker-start="url(#source-dot)" marker-end="url(#arrowhead)"/><line x1="500" y1="200" x2="700" y2="400" style="stroke: #2196F3; stroke-width: 2; stroke-dasharray: 6,4;" marker-start="url(#source-dot)" marker-end="url(#arrowhead)"/></svg>`;

// Uses stroke attribute (alternate SVG serialization format)
const SAMPLE_SVG_ATTR = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" role="img"><defs><marker id="arrowhead" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker><marker id="source-dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="8" markerHeight="8" markerUnits="userSpaceOnUse"><circle cx="5" cy="5" r="4" fill="context-stroke"/></marker></defs><rect x="0" y="0" width="1200" height="800" style="fill: #1a1f36;"/><line x1="100" y1="200" x2="300" y2="400" stroke="#00C853" stroke-width="2" stroke-dasharray="6,4" marker-start="url(#source-dot)" marker-end="url(#arrowhead)"/><line x1="500" y1="200" x2="700" y2="400" stroke="#2196F3" stroke-width="2" stroke-dasharray="6,4" marker-start="url(#source-dot)" marker-end="url(#arrowhead)"/></svg>`;

function parseSvg(svgString: string): Document {
	return new DOMParser().parseFromString(svgString, 'image/svg+xml');
}

describe('slugify', () => {
	it('converts normal text to slug', () => {
		expect(slugify('Acme Corp')).toBe('acme-corp');
	});

	it('strips ampersands and special characters', () => {
		expect(slugify('AT&T / Wireless')).toBe('att-wireless');
	});

	it('returns empty string for whitespace-only input', () => {
		expect(slugify('  ')).toBe('');
	});

	it('trims leading and trailing hyphens', () => {
		expect(slugify('---hello---')).toBe('hello');
	});

	it('strips dangerous filesystem characters', () => {
		expect(slugify('Hello/World\\Foo:Bar')).toBe('helloworldfoobar');
	});
});

describe('generateFilename', () => {
	it('uses customer name when available', () => {
		expect(generateFilename('Acme Corp', 'My Diagram', 'png')).toBe('acme-corp.png');
	});

	it('falls back to title when customer name is empty', () => {
		expect(generateFilename('', 'Q4 Architecture', 'svg')).toBe('q4-architecture.svg');
	});

	it('falls back to generic name when both are empty', () => {
		expect(generateFilename('', '', 'png')).toBe('integration-diagram.png');
	});

	it('falls back to title when customer name slugifies to empty', () => {
		expect(generateFilename('!!!', 'Q4 Arch', 'png')).toBe('q4-arch.png');
	});

	it('falls back to generic when both slugify to empty', () => {
		expect(generateFilename('!!!', '???', 'svg')).toBe('integration-diagram.svg');
	});
});

describe('arrayBufferToBase64', () => {
	it('converts a known byte sequence to correct base64', () => {
		const bytes = new Uint8Array([72, 101, 108, 108, 111]);
		expect(arrayBufferToBase64(bytes.buffer)).toBe('SGVsbG8=');
	});

	it('handles empty buffer', () => {
		const empty = new Uint8Array([]);
		expect(arrayBufferToBase64(empty.buffer)).toBe('');
	});
});

describe('injectFont', () => {
	it('inserts a style element as first child of SVG', () => {
		const doc = parseSvg(SAMPLE_SVG);
		injectFont(doc, 'TESTFONT');
		expect(doc.querySelector('style')).not.toBeNull();
		expect(doc.documentElement.firstElementChild?.tagName).toBe('style');
	});

	it('contains font-family Inter and format woff2 and font-weight 100 900', () => {
		const doc = parseSvg(SAMPLE_SVG);
		injectFont(doc, 'TESTFONT');
		const content = doc.querySelector('style')?.textContent ?? '';
		expect(content).toContain("font-family: 'Inter'");
		expect(content).toContain('font-weight: 100 900');
		expect(content).toContain("format('woff2')");
	});

	it('preserves existing SVG child elements', () => {
		const doc = parseSvg(SAMPLE_SVG);
		injectFont(doc, 'TESTFONT');
		expect(doc.querySelector('defs')).not.toBeNull();
		expect(doc.querySelector('rect')).not.toBeNull();
		expect(doc.querySelectorAll('line').length).toBe(2);
	});
});

describe('fixContextStroke', () => {
	it('reads stroke from inline style (real renderer output)', () => {
		const doc = parseSvg(SAMPLE_SVG);
		fixContextStroke(doc);
		expect(doc.querySelector('#arrowhead-00C853')).not.toBeNull();
		expect(doc.querySelector('#arrowhead-2196F3')).not.toBeNull();
		expect(doc.querySelector('#source-dot-00C853')).not.toBeNull();
		expect(doc.querySelector('#source-dot-2196F3')).not.toBeNull();
	});

	it('reads stroke from attribute (alternate serialization)', () => {
		const doc = parseSvg(SAMPLE_SVG_ATTR);
		fixContextStroke(doc);
		expect(doc.querySelector('#arrowhead-00C853')).not.toBeNull();
		expect(doc.querySelector('#arrowhead-2196F3')).not.toBeNull();
	});

	it('sets explicit fill color on cloned marker children', () => {
		const doc = parseSvg(SAMPLE_SVG);
		fixContextStroke(doc);
		expect(doc.querySelector('#arrowhead-00C853 path')?.getAttribute('fill')).toBe('#00C853');
		expect(doc.querySelector('#source-dot-00C853 circle')?.getAttribute('fill')).toBe('#00C853');
	});

	it('rewrites line marker references to color-specific markers', () => {
		const doc = parseSvg(SAMPLE_SVG);
		fixContextStroke(doc);
		const lines = doc.querySelectorAll('line');
		expect(lines[0].getAttribute('marker-end')).toBe('url(#arrowhead-00C853)');
		expect(lines[0].getAttribute('marker-start')).toBe('url(#source-dot-00C853)');
		expect(lines[1].getAttribute('marker-end')).toBe('url(#arrowhead-2196F3)');
		expect(lines[1].getAttribute('marker-start')).toBe('url(#source-dot-2196F3)');
	});

	it('preserves non-marker content', () => {
		const doc = parseSvg(SAMPLE_SVG);
		fixContextStroke(doc);
		expect(doc.querySelector('rect')).not.toBeNull();
	});
});

describe('ensureSvgDimensions', () => {
	it('adds width and height when SVG has viewBox but no width/height', () => {
		const doc = parseSvg(
			`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800"><rect/></svg>`,
		);
		ensureSvgDimensions(doc);
		expect(doc.documentElement.getAttribute('width')).toBe('1200');
		expect(doc.documentElement.getAttribute('height')).toBe('800');
	});

	it('preserves existing width/height attributes', () => {
		const doc = parseSvg(
			`<svg xmlns="http://www.w3.org/2000/svg" width="500" height="300" viewBox="0 0 1200 800"><rect/></svg>`,
		);
		ensureSvgDimensions(doc);
		expect(doc.documentElement.getAttribute('width')).toBe('500');
		expect(doc.documentElement.getAttribute('height')).toBe('300');
	});
});

describe('svgToDataUrl', () => {
	it('returns a string starting with "data:image/svg+xml;base64,"', () => {
		const result = svgToDataUrl('<svg></svg>');
		expect(result).toMatch(/^data:image\/svg\+xml;base64,/);
	});

	it('handles Unicode characters without throwing', () => {
		expect(() => svgToDataUrl('<svg><text>K\u00f6nig</text></svg>')).not.toThrow();
		const result = svgToDataUrl('<svg><text>K\u00f6nig</text></svg>');
		expect(result).toMatch(/^data:image\/svg\+xml;base64,/);
	});
});

describe('validateImageDataUrls', () => {
	it('returns true when all image hrefs start with data:', () => {
		const doc = parseSvg(
			`<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,abc"/></svg>`,
		);
		expect(validateImageDataUrls(doc)).toBe(true);
	});

	it('returns false when an image has an http:// href', () => {
		const doc = parseSvg(
			`<svg xmlns="http://www.w3.org/2000/svg"><image href="https://logo.dev/logo.png"/></svg>`,
		);
		expect(validateImageDataUrls(doc)).toBe(false);
	});

	it('returns true when SVG has no image elements', () => {
		const doc = parseSvg(`<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>`);
		expect(validateImageDataUrls(doc)).toBe(true);
	});
});
