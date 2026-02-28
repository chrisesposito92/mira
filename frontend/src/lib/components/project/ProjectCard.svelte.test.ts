import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import ProjectCard from './ProjectCard.svelte';

const baseProject = {
	id: '1',
	user_id: 'u1',
	name: 'Test Project',
	customer_name: 'Acme Corp',
	description: 'A test project description',
	org_connection_id: null,
	default_model_id: null,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-06-15T12:00:00Z',
};

describe('ProjectCard', () => {
	it('renders project name and customer', () => {
		render(ProjectCard, { props: { project: baseProject } });
		expect(screen.getAllByText('Test Project').length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText('Acme Corp').length).toBeGreaterThanOrEqual(1);
	});

	it('renders description', () => {
		render(ProjectCard, { props: { project: baseProject } });
		expect(screen.getAllByText('A test project description').length).toBeGreaterThanOrEqual(1);
	});

	it('shows "No description" when description is null', () => {
		render(ProjectCard, {
			props: { project: { ...baseProject, description: null } },
		});
		expect(screen.getAllByText('No description').length).toBeGreaterThanOrEqual(1);
	});

	it('renders formatted date', () => {
		render(ProjectCard, { props: { project: baseProject } });
		expect(screen.getAllByText(/Jun 15, 2024/).length).toBeGreaterThanOrEqual(1);
	});

	it('renders as a clickable button', () => {
		render(ProjectCard, { props: { project: baseProject } });
		const buttons = screen.getAllByRole('button');
		expect(buttons.length).toBeGreaterThanOrEqual(1);
	});
});
