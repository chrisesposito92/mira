export type DocProcessingStage = 'extracting' | 'chunking' | 'embedding' | 'storing';

export type DocWsMessage =
	| { type: 'doc_processing_started'; document_id: string; filename: string; stage: 'extracting' }
	| {
			type: 'doc_processing_progress';
			document_id: string;
			stage: DocProcessingStage;
			detail?: string;
	  }
	| { type: 'doc_processing_complete'; document_id: string; chunk_count: number }
	| { type: 'doc_processing_error'; document_id: string; error: string }
	| { type: 'ping' };

export interface DocumentUploadProgress {
	documentId: string | null;
	filename: string;
	phase: 'uploading' | 'processing' | 'complete' | 'error';
	uploadPercent: number;
	processingStage: DocProcessingStage | null;
	chunkCount: number | null;
	error: string | null;
}

export const DOC_PROCESSING_STAGES: DocProcessingStage[] = [
	'extracting',
	'chunking',
	'embedding',
	'storing',
];
