/** Diagram types for the integration architecture diagrammer. */

export interface DiagramSystem {
	id: string;
	component_library_id: string | null;
	name: string;
	logo_base64: string | null;
	x: number;
	y: number;
	category: string | null;
	role?: 'prospect' | 'hub' | 'system' | null;
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

/** Lightweight diagram for list queries -- excludes content JSONB. */
export interface DiagramListItem {
	id: string;
	user_id: string;
	customer_name: string;
	title: string;
	project_id: string | null;
	schema_version: number;
	thumbnail_base64: string | null;
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

/** Positioned system with computed layout coordinates. */
export interface PositionedSystem {
	system: DiagramSystem;
	x: number;
	y: number;
	width: number;
	height: number;
}

/** Category group card containing multiple positioned systems. */
export interface PositionedGroup {
	category: string;
	systems: PositionedSystem[];
	x: number;
	y: number;
	width: number;
	height: number;
}

/** Node-level position data for connection anchor lookup. */
export interface NodePositionMap {
	[systemId: string]: { x: number; y: number; width: number; height: number };
}

/** Complete layout result from the layout algorithm. */
export interface LayoutResult {
	hub: { x: number; y: number; width: number; height: number };
	prospect: PositionedSystem;
	groups: PositionedGroup[];
	standalone: PositionedSystem[];
	/** Flat lookup of all node bounding boxes by system ID plus 'hub' key. */
	nodePositions: NodePositionMap;
}
