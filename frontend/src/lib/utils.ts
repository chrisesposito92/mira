import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export type WithElementRef<T, E extends HTMLElement = HTMLElement> = T & {
	ref?: E | null;
};

export type WithoutChildrenOrChild<T> = T extends infer U ? Omit<U, 'children' | 'child'> : never;

export type WithoutChildren<T> = Omit<T, 'children'>;

export type WithoutChild<T> = Omit<T, 'child'>;

export function snakeToTitle(s: string): string {
	return s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function capitalize(s: string): string {
	return s.charAt(0).toUpperCase() + s.slice(1);
}

export function formatDate(dateStr: string): string {
	// For date-only strings like "2024-06-01", split manually to avoid
	// timezone shift (JS Date parses these as UTC, shifting the day in non-UTC zones)
	const match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
	if (match) {
		const [, y, m, d] = match;
		return new Date(+y, +m - 1, +d).toLocaleDateString();
	}
	return new Date(dateStr).toLocaleDateString();
}

export function formatDateTime(dateStr: string): string {
	return new Date(dateStr).toLocaleString();
}

/** Debounce a function call by `delay` milliseconds. Repeated calls reset the timer. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function debounce<T extends (...args: any[]) => any>(
	fn: T,
	delay: number,
): (...args: Parameters<T>) => void {
	let timeoutId: ReturnType<typeof setTimeout> | null = null;
	return (...args: Parameters<T>) => {
		if (timeoutId) clearTimeout(timeoutId);
		timeoutId = setTimeout(() => fn(...args), delay);
	};
}

/** Format a date string as a relative time (e.g., "2 hours ago", "just now").
 *  Handles future timestamps gracefully by returning "just now". */
export function formatRelativeTime(dateStr: string): string {
	const date = new Date(dateStr);
	const now = new Date();
	const diffMs = now.getTime() - date.getTime();

	if (diffMs < 0) return 'just now';

	const diffSec = Math.floor(diffMs / 1000);
	const diffMin = Math.floor(diffSec / 60);
	const diffHour = Math.floor(diffMin / 60);
	const diffDay = Math.floor(diffHour / 24);

	if (diffSec < 60) return 'just now';
	if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? '' : 's'} ago`;
	if (diffHour < 24) return `${diffHour} hour${diffHour === 1 ? '' : 's'} ago`;
	return `${diffDay} day${diffDay === 1 ? '' : 's'} ago`;
}
