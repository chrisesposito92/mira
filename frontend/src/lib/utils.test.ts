import { describe, it, expect } from 'vitest';
import { cn } from './utils.js';

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
