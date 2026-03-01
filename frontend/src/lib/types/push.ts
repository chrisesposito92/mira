// Push WebSocket message types (discriminated union)
export type PushWsMessage =
	| { type: 'push_started'; total: number }
	| {
			type: 'push_progress';
			entity_id: string;
			entity_type: string;
			success: boolean;
			m3ter_id: string | null;
			error: string | null;
			completed: number;
			total: number;
	  }
	| { type: 'push_complete'; total: number; succeeded: number; failed: number; skipped: number }
	| { type: 'push_error'; message: string };

// Per-object progress tracking
export interface PushObjectProgress {
	entityId: string;
	entityType: string;
	status: 'pending' | 'pushing' | 'pushed' | 'push_failed';
	m3terId?: string;
	error?: string;
}

// Active push session state
export interface PushSession {
	active: boolean;
	total: number;
	completed: number;
	succeeded: number;
	failed: number;
	items: PushObjectProgress[];
}

// REST response types
export interface PushResultResponse {
	entity_id: string;
	entity_type: string;
	success: boolean;
	m3ter_id?: string;
	error?: string;
}

export interface BulkPushResultResponse {
	results: PushResultResponse[];
	total: number;
	succeeded: number;
	failed: number;
	skipped: number;
}

export interface PushStatusResponse {
	org_connected: boolean;
	eligible_count: number;
	pushed_count: number;
	total_count: number;
	entity_breakdown: Record<string, { eligible: number; pushed: number; total: number }>;
}
