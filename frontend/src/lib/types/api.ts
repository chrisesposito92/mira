/** API request/response types mirroring backend Pydantic schemas. */

import type { UseCaseStatus, BillingFrequency, EntityType, ObjectStatus } from './index.js';

export type ConnectionStatus = 'active' | 'inactive' | 'error';

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed';

// --- Projects ---

export interface Project {
	id: string;
	user_id: string;
	name: string;
	customer_name: string | null;
	description: string | null;
	org_connection_id: string | null;
	default_model_id: string | null;
	created_at: string;
	updated_at: string;
}

export interface ProjectCreate {
	name: string;
	customer_name?: string | null;
	description?: string | null;
	org_connection_id?: string | null;
	default_model_id?: string | null;
}

export interface ProjectUpdate {
	name?: string | null;
	customer_name?: string | null;
	description?: string | null;
	org_connection_id?: string | null;
	default_model_id?: string | null;
}

// --- Use Cases ---

export interface UseCase {
	id: string;
	project_id: string;
	title: string;
	description: string | null;
	status: UseCaseStatus;
	contract_start_date: string | null;
	billing_frequency: BillingFrequency | null;
	currency: string;
	target_billing_model: string | null;
	notes: string | null;
	created_at: string;
	updated_at: string;
}

export interface UseCaseCreate {
	title: string;
	description?: string | null;
	contract_start_date?: string | null;
	billing_frequency?: BillingFrequency | null;
	currency?: string;
	target_billing_model?: string | null;
	notes?: string | null;
}

export interface UseCaseUpdate {
	title?: string | null;
	description?: string | null;
	status?: UseCaseStatus | null;
	contract_start_date?: string | null;
	billing_frequency?: BillingFrequency | null;
	currency?: string | null;
	target_billing_model?: string | null;
	notes?: string | null;
}

// --- Documents ---

export interface Document {
	id: string;
	project_id: string;
	filename: string;
	file_type: string;
	storage_path: string;
	processing_status: DocumentStatus;
	chunk_count: number;
	file_size_bytes: number | null;
	error_message: string | null;
	created_at: string;
	updated_at: string;
}

// --- Org Connections ---

export interface OrgConnection {
	id: string;
	user_id: string;
	org_id: string;
	org_name: string;
	api_url: string;
	status: ConnectionStatus;
	last_tested_at: string | null;
	created_at: string;
	updated_at: string;
}

export interface OrgConnectionCreate {
	org_id: string;
	org_name: string;
	api_url?: string;
	client_id: string;
	client_secret: string;
}

export interface OrgConnectionUpdate {
	org_name?: string | null;
	api_url?: string | null;
	client_id?: string | null;
	client_secret?: string | null;
}

export interface OrgConnectionTestResult {
	success: boolean;
	message: string;
	tested_at: string;
}

// --- Generated Objects ---

export interface GeneratedObject {
	id: string;
	use_case_id: string;
	entity_type: EntityType;
	name: string | null;
	code: string | null;
	status: ObjectStatus;
	data: Record<string, unknown> | null;
	validation_errors: Array<{ field: string; message: string; severity: string }> | null;
	m3ter_id: string | null;
	depends_on: string[] | null;
	created_at: string;
	updated_at: string;
}

export interface GeneratedObjectUpdate {
	name?: string;
	code?: string;
	status?: ObjectStatus;
	data?: Record<string, unknown>;
}

export interface BulkStatusUpdate {
	ids: string[];
	status: ObjectStatus;
}
