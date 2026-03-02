import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import UploadProgressBar from './UploadProgressBar.svelte';
import type { DocumentUploadProgress } from '$lib/types';

function makeProgress(overrides: Partial<DocumentUploadProgress> = {}): DocumentUploadProgress {
	return {
		documentId: 'doc-1',
		filename: 'test.pdf',
		phase: 'uploading',
		uploadPercent: 0,
		processingStage: null,
		chunkCount: null,
		error: null,
		...overrides,
	};
}

describe('UploadProgressBar', () => {
	it('renders upload percentage during uploading phase', () => {
		const progress = makeProgress({ phase: 'uploading', uploadPercent: 45 });
		render(UploadProgressBar, { props: { progress } });
		expect(screen.getByText('Uploading... 45%')).toBeTruthy();
	});

	it('renders upload progress bar at correct width', () => {
		const progress = makeProgress({ phase: 'uploading', uploadPercent: 75 });
		const { container } = render(UploadProgressBar, { props: { progress } });
		const bar = container.querySelector('[style*="width: 75%"]');
		expect(bar).toBeTruthy();
	});

	it('renders processing stage indicators', () => {
		const progress = makeProgress({
			phase: 'processing',
			processingStage: 'chunking',
		});
		render(UploadProgressBar, { props: { progress } });
		expect(screen.getByText('extracting')).toBeTruthy();
		expect(screen.getByText('chunking')).toBeTruthy();
		expect(screen.getByText('embedding')).toBeTruthy();
		expect(screen.getByText('storing')).toBeTruthy();
	});

	it('renders complete phase with chunk count', () => {
		const progress = makeProgress({
			phase: 'complete',
			chunkCount: 42,
		});
		render(UploadProgressBar, { props: { progress } });
		expect(screen.getByText(/Processing complete/)).toBeTruthy();
		expect(screen.getByText(/42 chunks/)).toBeTruthy();
	});

	it('renders complete phase without chunk count', () => {
		const progress = makeProgress({
			phase: 'complete',
			chunkCount: null,
		});
		render(UploadProgressBar, { props: { progress } });
		expect(screen.getByText('Processing complete')).toBeTruthy();
	});

	it('renders error message', () => {
		const progress = makeProgress({
			phase: 'error',
			error: 'Unsupported file format',
		});
		render(UploadProgressBar, { props: { progress } });
		expect(screen.getByText('Unsupported file format')).toBeTruthy();
	});

	it('renders fallback error message when error is null', () => {
		const progress = makeProgress({
			phase: 'error',
			error: null,
		});
		render(UploadProgressBar, { props: { progress } });
		expect(screen.getByText('Processing failed')).toBeTruthy();
	});
});
