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
