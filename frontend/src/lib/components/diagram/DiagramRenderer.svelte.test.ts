import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import DiagramRenderer from './DiagramRenderer.svelte';
import type { DiagramContent, ComponentLibraryItem } from '$types/diagram.js';

/** Minimal content with no systems or connections. */
function makeMinimalContent(): DiagramContent {
	return {
		systems: [],
		connections: [],
		settings: {
			background_color: '#1a1f36',
			show_labels: true,
		},
	};
}

/** Content with a system and a connection. */
function makeContentWithConnection(): DiagramContent {
	return {
		systems: [
			{
				id: 'prospect-1',
				component_library_id: null,
				name: 'My Platform',
				logo_base64: null,
				x: 0,
				y: 0,
				category: null,
				role: 'prospect',
			},
			{
				id: 'sys-1',
				component_library_id: null,
				name: 'Stripe',
				logo_base64: 'monogram:ST:#FF5722',
				x: 0,
				y: 0,
				category: null,
				role: 'system',
			},
		],
		connections: [
			{
				id: 'conn-1',
				source_id: 'sys-1',
				target_id: 'prospect-1',
				label: 'Payments',
				direction: 'unidirectional',
				connection_type: 'api',
			},
		],
		settings: {
			background_color: '#1a1f36',
			show_labels: true,
		},
	};
}

const emptyLibrary: ComponentLibraryItem[] = [];

describe('DiagramRenderer', () => {
	it('renders an <svg> element with viewBox 0 0 1200 800', () => {
		const { container } = render(DiagramRenderer, {
			props: { content: makeMinimalContent(), componentLibrary: emptyLibrary },
		});
		const svg = container.querySelector('svg');
		expect(svg).not.toBeNull();
		expect(svg!.getAttribute('viewBox')).toBe('0 0 1200 800');
	});

	it('contains a <rect> background with fill #1a1f36 as first child of SVG', () => {
		const { container } = render(DiagramRenderer, {
			props: { content: makeMinimalContent(), componentLibrary: emptyLibrary },
		});
		const svg = container.querySelector('svg');
		// The first <rect> (after <defs>) should be the background
		const rects = svg!.querySelectorAll('rect');
		const bgRect = rects[0];
		expect(bgRect).toBeTruthy();
		const style = bgRect.getAttribute('style') || '';
		// jsdom normalizes hex to rgb: #1a1f36 = rgb(26, 31, 54)
		expect(style.includes('#1a1f36') || style.includes('rgb(26, 31, 54)')).toBe(true);
		expect(bgRect.getAttribute('width')).toBe('1200');
		expect(bgRect.getAttribute('height')).toBe('800');
	});

	it('SVG does NOT have CSS background style on the svg element', () => {
		const { container } = render(DiagramRenderer, {
			props: { content: makeMinimalContent(), componentLibrary: emptyLibrary },
		});
		const svg = container.querySelector('svg');
		const svgStyle = svg!.getAttribute('style') || '';
		expect(svgStyle).not.toContain('background');
	});

	it('SVG output does NOT contain foreignObject', () => {
		const { container } = render(DiagramRenderer, {
			props: {
				content: makeContentWithConnection(),
				componentLibrary: emptyLibrary,
			},
		});
		const foreignObjects = container.querySelectorAll('foreignObject');
		expect(foreignObjects.length).toBe(0);
	});

	it('renders with empty systems/connections (just hub + prospect)', () => {
		const { container } = render(DiagramRenderer, {
			props: { content: makeMinimalContent(), componentLibrary: emptyLibrary },
		});
		// Should contain m3ter hub text
		expect(container.textContent).toContain('m3ter');
		// Prospect name "Your Product/Platform" (21 chars) is truncated to 16 chars + "..."
		// by truncateSvgText(name, MAX_SYSTEM_NAME_CHARS)
		expect(container.textContent).toContain('Your Product/Pla...');
	});
});
