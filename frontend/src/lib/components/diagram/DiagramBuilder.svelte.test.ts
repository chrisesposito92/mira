import { describe, it, expect } from 'vitest';

describe('Auto-save version counter logic', () => {
	it('increments version on each save call', () => {
		const counter = { value: 0 };
		const v1 = ++counter.value;
		const v2 = ++counter.value;
		expect(v1).toBe(1);
		expect(v2).toBe(2);
		expect(v2).not.toBe(v1);
	});

	it('detects stale save when version has advanced', () => {
		let saveVersion = 0;
		const capturedVersion = ++saveVersion;
		++saveVersion;
		const isStale = capturedVersion !== saveVersion;
		expect(isStale).toBe(true);
	});

	it('does not detect stale when no concurrent save', () => {
		let saveVersion = 0;
		const capturedVersion = ++saveVersion;
		const isStale = capturedVersion !== saveVersion;
		expect(isStale).toBe(false);
	});
});

describe('Thumbnail throttle logic', () => {
	it('allows thumbnail generation when interval exceeded', () => {
		const lastThumbnailTime = 0;
		const now = 15_000;
		const shouldGenerate = now - lastThumbnailTime > 10_000;
		expect(shouldGenerate).toBe(true);
	});

	it('skips thumbnail generation within interval', () => {
		const lastThumbnailTime = 10_000;
		const now = 15_000;
		const shouldGenerate = now - lastThumbnailTime > 10_000;
		expect(shouldGenerate).toBe(false);
	});
});
