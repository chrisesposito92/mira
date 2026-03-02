import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/svelte';
import UseCaseResultCard from './UseCaseResultCard.svelte';
import type { GeneratedUseCase } from '$lib/types/generator.js';

afterEach(() => cleanup());

const baseUseCase: GeneratedUseCase = {
	title: 'API Usage Billing',
	description: 'Bill customers based on API call volume with tiered pricing.',
	billing_frequency: 'monthly',
	currency: 'USD',
	target_billing_model: 'tiered',
	notes: null,
};

describe('UseCaseResultCard', () => {
	it('renders use case title', () => {
		const onToggle = vi.fn();
		render(UseCaseResultCard, {
			props: { useCase: baseUseCase, selected: false, onToggle },
		});
		expect(screen.getByText('API Usage Billing')).toBeTruthy();
	});

	it('renders description text', () => {
		const onToggle = vi.fn();
		render(UseCaseResultCard, {
			props: { useCase: baseUseCase, selected: false, onToggle },
		});
		expect(
			screen.getAllByText('Bill customers based on API call volume with tiered pricing.').length,
		).toBeGreaterThanOrEqual(1);
	});

	it('renders billing frequency badge', () => {
		const onToggle = vi.fn();
		render(UseCaseResultCard, {
			props: { useCase: baseUseCase, selected: false, onToggle },
		});
		expect(screen.getAllByText('Monthly').length).toBeGreaterThanOrEqual(1);
	});

	it('renders currency badge', () => {
		const onToggle = vi.fn();
		render(UseCaseResultCard, {
			props: { useCase: baseUseCase, selected: false, onToggle },
		});
		expect(screen.getAllByText('USD').length).toBeGreaterThanOrEqual(1);
	});

	it('renders target billing model badge', () => {
		const onToggle = vi.fn();
		render(UseCaseResultCard, {
			props: { useCase: baseUseCase, selected: false, onToggle },
		});
		expect(screen.getAllByText('tiered').length).toBeGreaterThanOrEqual(1);
	});

	it('calls onToggle when card is clicked', async () => {
		const onToggle = vi.fn();
		render(UseCaseResultCard, {
			props: { useCase: baseUseCase, selected: false, onToggle },
		});
		const buttons = screen.getAllByRole('button');
		await fireEvent.click(buttons[0]);
		expect(onToggle).toHaveBeenCalledOnce();
	});

	it('applies ring styling when selected', () => {
		const onToggle = vi.fn();
		const { container } = render(UseCaseResultCard, {
			props: { useCase: baseUseCase, selected: true, onToggle },
		});
		const card = container.querySelector('[data-slot="card"]');
		expect(card?.className).toContain('ring-2');
	});

	it('does not render billing model badge when null', () => {
		const onToggle = vi.fn();
		const uc = { ...baseUseCase, target_billing_model: null };
		render(UseCaseResultCard, {
			props: { useCase: uc, selected: false, onToggle },
		});
		expect(screen.queryAllByText('tiered')).toHaveLength(0);
	});

	it('does not render billing frequency badge when null', () => {
		const onToggle = vi.fn();
		const uc = { ...baseUseCase, billing_frequency: null };
		render(UseCaseResultCard, {
			props: { useCase: uc, selected: false, onToggle },
		});
		expect(screen.queryAllByText('Monthly')).toHaveLength(0);
	});
});
