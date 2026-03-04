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
