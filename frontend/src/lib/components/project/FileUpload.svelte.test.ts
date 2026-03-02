import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import FileUpload from './FileUpload.svelte';
import type { Document } from '$lib/types';

const baseDoc: Document = {
	id: 'doc-1',
	project_id: 'proj-1',
	filename: 'report.pdf',
	file_type: 'pdf',
	file_size_bytes: 2048,
	storage_path: '/uploads/report.pdf',
	processing_status: 'ready',
	chunk_count: 10,
	error_message: null,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z',
};

describe('FileUpload', () => {
	it('renders drop zone with instructions', () => {
		render(FileUpload);
		expect(screen.getByText('Drop file here or click to browse')).toBeTruthy();
		expect(screen.getByText('PDF, DOCX, TXT, CSV')).toBeTruthy();
	});

	it('renders document list with file info', () => {
		render(FileUpload, {
			props: {
				documents: [baseDoc],
			},
		});
		expect(screen.getByText('report.pdf')).toBeTruthy();
		expect(screen.getByText(/2\.0 KB/)).toBeTruthy();
		expect(screen.getByText(/10 chunks/)).toBeTruthy();
	});

	it('renders multiple documents', () => {
		const docs = [
			baseDoc,
			{ ...baseDoc, id: 'doc-2', filename: 'data.csv', file_type: 'csv', chunk_count: 5 },
		];
		const { container } = render(FileUpload, { props: { documents: docs } });
		expect(screen.getAllByText('report.pdf').length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText('data.csv').length).toBeGreaterThanOrEqual(1);
		// Verify both doc rows are rendered
		const docRows = container.querySelectorAll('.divide-y > div');
		expect(docRows.length).toBe(2);
	});

	it('shows processing text when uploading', () => {
		render(FileUpload, { props: { uploading: true } });
		expect(screen.getAllByText('Processing...').length).toBeGreaterThanOrEqual(1);
	});

	it('applies disabled styling when uploading', () => {
		const { container } = render(FileUpload, { props: { uploading: true } });
		// The drop zone gets pointer-events-none + opacity-60 when uploading
		const dropZone = container.querySelector('.pointer-events-none');
		expect(dropZone).toBeTruthy();
	});

	it('renders status badges for documents', () => {
		const docs = [
			{ ...baseDoc, processing_status: 'ready' as const },
			{ ...baseDoc, id: 'doc-2', filename: 'pending.pdf', processing_status: 'pending' as const },
		];
		render(FileUpload, { props: { documents: docs } });
		expect(screen.getAllByText('Ready').length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText('Pending').length).toBeGreaterThanOrEqual(1);
	});

	it('shows processing spinner for documents being processed', () => {
		const docs = [
			{
				...baseDoc,
				processing_status: 'processing' as const,
			},
		];
		const { container } = render(FileUpload, { props: { documents: docs } });
		expect(screen.getAllByText('Processing...').length).toBeGreaterThanOrEqual(1);
		const spinner = container.querySelector('.animate-spin');
		expect(spinner).toBeTruthy();
	});

	it('calls ondelete callback when delete button clicked', async () => {
		const ondelete = vi.fn();
		render(FileUpload, {
			props: { documents: [baseDoc], ondelete },
		});
		// The drop zone is button[0], delete is button[1]
		const buttons = screen.getAllByRole('button');
		const deleteButton = buttons[buttons.length - 1];
		await fireEvent.click(deleteButton);
		expect(ondelete).toHaveBeenCalledWith('doc-1');
	});

	it('renders upload progress bar when uploadProgress is provided', () => {
		render(FileUpload, {
			props: {
				uploadProgress: {
					documentId: null,
					filename: 'test.pdf',
					phase: 'uploading' as const,
					uploadPercent: 50,
					processingStage: null,
					chunkCount: null,
					error: null,
				},
			},
		});
		expect(screen.getByText('Uploading... 50%')).toBeTruthy();
	});

	it('does not render document list when no documents', () => {
		const { container } = render(FileUpload, { props: { documents: [] } });
		const docList = container.querySelector('.divide-y');
		expect(docList).toBeNull();
	});
});
