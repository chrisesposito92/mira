/** Diagram types for the integration architecture diagrammer. */

export interface DiagramSystem {
	id: string;
	component_library_id: string | null;
	name: string;
	logo_base64: string | null;
	x: number;
	y: number;
	category: string | null;
}

export interface DiagramConnection {
	id: string;
	source_id: string;
	target_id: string;
	label: string;
	direction: 'unidirectional' | 'bidirectional';
	connection_type: 'native_connector' | 'webhook_api' | 'custom_build' | 'api';
}

export interface DiagramSettings {
	background_color: string;
	show_labels: boolean;
}

export interface DiagramContent {
	systems: DiagramSystem[];
	connections: DiagramConnection[];
	settings: DiagramSettings;
}

/** Full diagram response -- used for GET /{id} detail view. */
export interface Diagram {
	id: string;
	user_id: string;
	customer_name: string;
	title: string;
	project_id: string | null;
	content: DiagramContent;
	schema_version: number;
	thumbnail_base64: string | null;
	created_at: string;
	updated_at: string;
}

/** Lightweight diagram for list queries -- excludes content and thumbnail_base64.
 *  Addresses review concern: list endpoint performance. */
export interface DiagramListItem {
	id: string;
	user_id: string;
	customer_name: string;
	title: string;
	project_id: string | null;
	schema_version: number;
	created_at: string;
	updated_at: string;
}

export interface DiagramCreate {
	customer_name: string;
	title?: string;
	project_id?: string | null;
}

/** Partial update for PATCH endpoint.
 *  Addresses review concern: missing update capability. */
export interface DiagramUpdate {
	customer_name?: string;
	title?: string;
	project_id?: string | null;
	content?: DiagramContent;
	schema_version?: number;
	thumbnail_base64?: string | null;
}

export interface ComponentLibraryItem {
	id: string;
	slug: string;
	name: string;
	domain: string;
	category: string;
	logo_base64: string | null;
	is_native_connector: boolean;
	display_order: number;
	created_at: string;
}
