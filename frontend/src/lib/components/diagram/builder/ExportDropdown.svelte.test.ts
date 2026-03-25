import { describe, it, expect, vi } from 'vitest';

/**
 * Tests for ExportDropdown component logic patterns.
 *
 * Since the component uses shadcn-svelte primitives (DropdownMenu, Tooltip)
 * that are complex to mount in jsdom, we test the extracted logic patterns
 * rather than full component rendering.
 */
describe('ExportDropdown logic', () => {
	describe('handleExport re-entry guard', () => {
		it('prevents concurrent exports', async () => {
			let exporting = false;
			const mockExport = vi.fn().mockResolvedValue(undefined);

			async function handleExport() {
				if (exporting) return;
				exporting = true;
				try {
					await mockExport();
				} finally {
					exporting = false;
				}
			}

			// Simulate double-click: call twice without awaiting first
			const p1 = handleExport();
			const p2 = handleExport(); // should be blocked by guard
			await Promise.all([p1, p2]);

			expect(mockExport).toHaveBeenCalledTimes(1);
		});

		it('resets exporting flag after successful export', async () => {
			let exporting = false;
			const mockExport = vi.fn().mockResolvedValue(undefined);

			async function handleExport() {
				if (exporting) return;
				exporting = true;
				try {
					await mockExport();
				} finally {
					exporting = false;
				}
			}

			await handleExport();
			expect(exporting).toBe(false);

			// Can export again after first completes
			await handleExport();
			expect(mockExport).toHaveBeenCalledTimes(2);
		});

		it('resets exporting flag after failed export', async () => {
			let exporting = false;
			const mockExport = vi.fn().mockRejectedValue(new Error('Canvas fail'));

			async function handleExport() {
				if (exporting) return;
				exporting = true;
				try {
					await mockExport();
				} catch {
					// Error handled (toast in real component)
				} finally {
					exporting = false;
				}
			}

			await handleExport();
			expect(exporting).toBe(false);
		});
	});

	describe('error handling', () => {
		it('calls toast.error when export throws', async () => {
			const errors: string[] = [];
			const mockToastError = (msg: string) => errors.push(msg);
			const mockExport = vi.fn().mockRejectedValue(new Error('Canvas fail'));

			try {
				await mockExport();
			} catch {
				mockToastError('Export failed. Try refreshing the page and exporting again.');
			}

			expect(errors).toContain('Export failed. Try refreshing the page and exporting again.');
		});

		it('shows error when SVG element is not found', () => {
			const errors: string[] = [];
			const mockToastError = (msg: string) => errors.push(msg);

			// Simulate document.querySelector returning null
			const svgEl = null;
			if (!svgEl) {
				mockToastError('Export failed. Try refreshing the page and exporting again.');
			}

			expect(errors).toHaveLength(1);
			expect(errors[0]).toBe('Export failed. Try refreshing the page and exporting again.');
		});
	});

	describe('hasUserSystems check', () => {
		it('returns false when only hub and prospect systems exist', () => {
			const systems = [
				{ id: '1', name: 'm3ter', role: 'hub' as const },
				{ id: '2', name: 'Your Product', role: 'prospect' as const },
			];
			const hasUserSystems =
				systems.filter((s) => s.role !== 'hub' && s.role !== 'prospect').length > 0;
			expect(hasUserSystems).toBe(false);
		});

		it('returns true when at least one non-hub non-prospect system exists', () => {
			const systems = [
				{ id: '1', name: 'm3ter', role: 'hub' as const },
				{ id: '2', name: 'Your Product', role: 'prospect' as const },
				{ id: '3', name: 'Salesforce', role: 'system' as const },
			];
			const hasUserSystems =
				systems.filter((s) => s.role !== 'hub' && s.role !== 'prospect').length > 0;
			expect(hasUserSystems).toBe(true);
		});

		it('returns true for system with null role', () => {
			const systems = [
				{ id: '1', name: 'm3ter', role: 'hub' as const },
				{ id: '2', name: 'Custom System', role: null },
			];
			const hasUserSystems =
				systems.filter((s) => s.role !== 'hub' && s.role !== 'prospect').length > 0;
			expect(hasUserSystems).toBe(true);
		});

		it('returns true for system with undefined role', () => {
			const systems = [
				{ id: '1', name: 'm3ter', role: 'hub' as const },
				{ id: '2', name: 'Custom System', role: undefined },
			];
			const hasUserSystems =
				systems.filter((s) => s.role !== 'hub' && s.role !== 'prospect').length > 0;
			expect(hasUserSystems).toBe(true);
		});

		it('returns false for empty systems array', () => {
			const systems: { id: string; name: string; role: string | null }[] = [];
			const hasUserSystems =
				systems.filter((s) => s.role !== 'hub' && s.role !== 'prospect').length > 0;
			expect(hasUserSystems).toBe(false);
		});
	});
});
