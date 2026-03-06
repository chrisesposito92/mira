import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import { userEvent } from '@testing-library/user-event';
import UseCaseMetadataPanel from './UseCaseMetadataPanel.svelte';
import type { UseCase } from '$lib/types';

const baseUseCase: UseCase = {
	id: 'uc-1',
	project_id: 'proj-1',
	title: 'Cloud Storage Billing',
	description: 'Usage-based billing for cloud storage',
	status: 'in_progress',
	billing_frequency: 'monthly',
	currency: 'USD',
	target_billing_model: 'tiered',
	contract_start_date: '2024-06-01',
	notes: 'Some notes here',
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-06-01T00:00:00Z',
};

const defaultProps = {
	useCase: baseUseCase,
	objectCount: 0,
	saving: false,
	onupdate: vi.fn().mockResolvedValue(baseUseCase),
	onreset: vi.fn().mockResolvedValue(undefined),
};

describe('UseCaseMetadataPanel', () => {
	it('renders expanded by default with content visible', () => {
		render(UseCaseMetadataPanel, { props: defaultProps });
		const trigger = screen.getAllByText('Use Case Details')[0];
		expect(trigger).toBeTruthy();
		// Content area should be visible (open = true by default)
		const content = document.querySelector('[data-collapsible-content]');
		expect(content?.hasAttribute('hidden')).toBe(false);
		expect(screen.getAllByText('Cloud Storage Billing').length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText('Monthly').length).toBeGreaterThanOrEqual(1);
	});

	it('collapses on click and hides content', async () => {
		const user = userEvent.setup();
		render(UseCaseMetadataPanel, { props: defaultProps });

		const trigger = screen.getAllByText('Use Case Details')[0];
		await user.click(trigger);

		const content = document.querySelector('[data-collapsible-content]');
		expect(content?.hasAttribute('hidden')).toBe(true);
	});

	it('shows edit button with pencil icon when expanded', async () => {
		const user = userEvent.setup();
		render(UseCaseMetadataPanel, { props: defaultProps });

		const trigger = screen.getAllByText('Use Case Details')[0];
		await user.click(trigger);

		const pencilSvg = document.querySelector('svg.lucide-pencil');
		expect(pencilSvg).toBeTruthy();
	});

	it('switches to edit mode when pencil button is clicked', async () => {
		const user = userEvent.setup();
		render(UseCaseMetadataPanel, { props: defaultProps });

		// Expand
		const trigger = screen.getAllByText('Use Case Details')[0];
		await user.click(trigger);

		// Click edit button
		const pencilSvg = document.querySelector('svg.lucide-pencil');
		const editButton = pencilSvg!.closest('button')!;
		await user.click(editButton);

		// Should show Save and Cancel buttons in edit mode
		await waitFor(() => {
			expect(screen.queryByText('Save')).toBeTruthy();
			expect(screen.queryByText('Cancel')).toBeTruthy();
		});
	});
});
