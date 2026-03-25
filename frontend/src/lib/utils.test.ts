import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { cn, debounce, formatRelativeTime } from './utils.js';

describe('cn', () => {
	it('merges class names', () => {
		expect(cn('foo', 'bar')).toBe('foo bar');
	});

	it('handles conditional classes', () => {
		const isHidden = false;
		expect(cn('base', isHidden && 'hidden', 'visible')).toBe('base visible');
	});

	it('deduplicates tailwind classes', () => {
		expect(cn('p-4', 'p-2')).toBe('p-2');
	});

	it('handles empty inputs', () => {
		expect(cn()).toBe('');
		expect(cn('')).toBe('');
		expect(cn(undefined)).toBe('');
	});

	it('merges conflicting tailwind utilities', () => {
		expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
	});
});

describe('debounce', () => {
	beforeEach(() => {
		vi.useFakeTimers();
	});
	afterEach(() => {
		vi.useRealTimers();
	});

	it('delays function execution by specified ms', () => {
		const fn = vi.fn();
		const debounced = debounce(fn, 500);
		debounced();
		expect(fn).not.toHaveBeenCalled();
		vi.advanceTimersByTime(500);
		expect(fn).toHaveBeenCalledOnce();
	});

	it('resets timer on repeated calls', () => {
		const fn = vi.fn();
		const debounced = debounce(fn, 500);
		debounced();
		vi.advanceTimersByTime(300);
		debounced();
		vi.advanceTimersByTime(300);
		expect(fn).not.toHaveBeenCalled();
		vi.advanceTimersByTime(200);
		expect(fn).toHaveBeenCalledOnce();
	});

	it('passes arguments to the original function', () => {
		const fn = vi.fn();
		const debounced = debounce(fn, 100);
		debounced('arg1', 'arg2');
		vi.advanceTimersByTime(100);
		expect(fn).toHaveBeenCalledWith('arg1', 'arg2');
	});
});

describe('formatRelativeTime', () => {
	it('returns "just now" for timestamps less than 60 seconds ago', () => {
		const now = new Date();
		const thirtySecsAgo = new Date(now.getTime() - 30 * 1000).toISOString();
		expect(formatRelativeTime(thirtySecsAgo)).toBe('just now');
	});

	it('returns minutes ago for timestamps 1-59 minutes ago', () => {
		const now = new Date();
		const fiveMinAgo = new Date(now.getTime() - 5 * 60 * 1000).toISOString();
		const result = formatRelativeTime(fiveMinAgo);
		expect(result).toMatch(/5 minutes ago/);
	});

	it('returns hours ago for timestamps 1-23 hours ago', () => {
		const now = new Date();
		const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString();
		const result = formatRelativeTime(twoHoursAgo);
		expect(result).toMatch(/2 hours ago/);
	});

	it('returns days ago for timestamps 1+ days ago', () => {
		const now = new Date();
		const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString();
		const result = formatRelativeTime(threeDaysAgo);
		expect(result).toMatch(/3 days ago/);
	});

	it('returns "just now" for future timestamps (graceful handling)', () => {
		const now = new Date();
		const inFuture = new Date(now.getTime() + 60 * 1000).toISOString();
		expect(formatRelativeTime(inFuture)).toBe('just now');
	});

	it('handles timestamps older than 30 days without crashing', () => {
		const now = new Date();
		const oldDate = new Date(now.getTime() - 45 * 24 * 60 * 60 * 1000).toISOString();
		const result = formatRelativeTime(oldDate);
		expect(result).toMatch(/\d+ days ago/);
	});
});
