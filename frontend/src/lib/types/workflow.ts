/** Workflow, WebSocket, and chat types mirroring backend schemas. */

import type { EntityType, WorkflowStatus, WorkflowType } from './index.js';

// --- LLM Models ---

export interface LlmModel {
	id: string;
	provider: string;
	display_name: string;
}

// --- Workflow ---

export interface Workflow {
	id: string;
	use_case_id: string;
	workflow_type: WorkflowType;
	status: WorkflowStatus;
	thread_id: string | null;
	model_id: string | null;
	interrupt_payload: Record<string, unknown> | null;
	error_message: string | null;
	started_at: string | null;
	completed_at: string | null;
	created_at: string;
	updated_at: string;
}

// --- Entities ---

export interface EntityItem {
	name: string;
	config: Record<string, unknown>;
}

export interface EntityError {
	field: string;
	message: string;
	severity: string;
}

// --- Entity Decisions (client → server via resume) ---
// Backend approval.py expects: {index: N, action: "approve"|"edit"|"reject", data?: {...}}

export interface EntityDecision {
	index: number;
	action: 'approve' | 'edit' | 'reject';
	data?: Record<string, unknown>;
}

// --- Clarification ---

export interface ClarificationOption {
	id: string;
	label: string;
	description?: string;
}

export interface ClarificationQuestion {
	id: string;
	question: string;
	options: ClarificationOption[];
	allows_free_text: boolean;
	recommendation?: string;
}

// Backend generation.py expects: {selected_option: <number index>, free_text?: string}
export interface ClarificationAnswer {
	selected_option?: number;
	free_text?: string;
}

// --- WebSocket Messages (server → client) ---

export interface WsStatusMessage {
	type: 'status';
	step: string;
	message: string;
}

export interface WsEntitiesMessage {
	type: 'entities';
	entity_type: EntityType;
	entities: Array<Record<string, unknown>>;
	errors: EntityError[];
}

export interface WsClarificationMessage {
	type: 'clarification';
	questions: ClarificationQuestion[];
}

export interface WsCompleteMessage {
	type: 'complete';
	message: string;
}

export interface WsErrorMessage {
	type: 'error';
	message: string;
}

export type WsServerMessage =
	| WsStatusMessage
	| WsEntitiesMessage
	| WsClarificationMessage
	| WsCompleteMessage
	| WsErrorMessage;

// --- WebSocket Messages (client → server) ---

export interface WsResumeMessage {
	type: 'resume';
	decisions: EntityDecision[];
}

export interface WsClarifyMessage {
	type: 'clarify';
	answers: ClarificationAnswer[];
}

export type WsClientMessage = WsResumeMessage | WsClarifyMessage;

// --- Chat Messages (frontend display model) ---

export interface ChatStatusMessage {
	id: string;
	type: 'status';
	step: string;
	message: string;
	timestamp: string;
}

export interface ChatEntitiesMessage {
	id: string;
	type: 'entities';
	entity_type: EntityType;
	entities: Array<Record<string, unknown>>;
	errors: EntityError[];
	timestamp: string;
}

export interface ChatClarificationMessage {
	id: string;
	type: 'clarification';
	questions: ClarificationQuestion[];
	timestamp: string;
}

export interface ChatUserDecisionMessage {
	id: string;
	type: 'user_decision';
	decisions: EntityDecision[];
	timestamp: string;
}

export interface ChatUserClarificationMessage {
	id: string;
	type: 'user_clarification';
	answers: ClarificationAnswer[];
	timestamp: string;
}

export interface ChatCompleteMessage {
	id: string;
	type: 'complete';
	message: string;
	timestamp: string;
}

export interface ChatErrorMessage {
	id: string;
	type: 'error';
	message: string;
	timestamp: string;
}

export type ChatMessage =
	| ChatStatusMessage
	| ChatEntitiesMessage
	| ChatClarificationMessage
	| ChatUserDecisionMessage
	| ChatUserClarificationMessage
	| ChatCompleteMessage
	| ChatErrorMessage;

// --- WebSocket Connection State ---

export type WsConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting';

// --- Chat Message Persistence ---

export interface ChatMessageCreate {
	role: 'user' | 'assistant' | 'system';
	content: string;
	metadata?: Record<string, unknown>;
}

export interface ChatMessageResponse {
	id: string;
	workflow_id: string;
	role: string;
	content: string;
	metadata: Record<string, unknown> | null;
	created_at: string;
}
