import type {
	OrgConnection,
	OrgConnectionCreate,
	OrgConnectionUpdate,
	OrgConnectionTestResult,
} from '$lib/types';
import type { OrgConnectionService } from '$lib/services/org-connections.js';

class OrgConnectionStore {
	connections = $state<OrgConnection[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);
	testResult = $state<OrgConnectionTestResult | null>(null);
	testing = $state(false);

	async loadConnections(service: OrgConnectionService) {
		this.loading = true;
		this.error = null;
		try {
			this.connections = await service.list();
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load connections';
		} finally {
			this.loading = false;
		}
	}

	async createConnection(service: OrgConnectionService, data: OrgConnectionCreate) {
		this.error = null;
		try {
			const conn = await service.create(data);
			this.connections = [...this.connections, conn];
			return conn;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to create connection';
			return null;
		}
	}

	async updateConnection(service: OrgConnectionService, id: string, data: OrgConnectionUpdate) {
		this.error = null;
		try {
			const updated = await service.update(id, data);
			this.connections = this.connections.map((c) => (c.id === id ? updated : c));
			return updated;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to update connection';
			return null;
		}
	}

	async deleteConnection(service: OrgConnectionService, id: string) {
		this.error = null;
		try {
			await service.delete(id);
			this.connections = this.connections.filter((c) => c.id !== id);
			return true;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to delete connection';
			return false;
		}
	}

	async testConnection(service: OrgConnectionService, id: string) {
		this.testing = true;
		this.testResult = null;
		this.error = null;
		try {
			this.testResult = await service.test(id);
			this.connections = this.connections.map((c) =>
				c.id === id
					? {
							...c,
							status: this.testResult!.success ? ('active' as const) : ('error' as const),
							last_tested_at: this.testResult!.tested_at,
						}
					: c,
			);
			return this.testResult;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to test connection';
			return null;
		} finally {
			this.testing = false;
		}
	}

	clear() {
		this.connections = [];
		this.loading = false;
		this.error = null;
		this.testResult = null;
		this.testing = false;
	}
}

export const orgConnectionStore = new OrgConnectionStore();
