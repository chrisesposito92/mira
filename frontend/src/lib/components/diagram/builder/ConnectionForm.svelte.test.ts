import { describe, it, expect } from 'vitest';
import { getSuggestionsForSystem, CATEGORY_SUGGESTIONS, HUB_ENDPOINT } from './suggestions.js';
import type { DiagramSystem, ComponentLibraryItem } from '$lib/types';

/**
 * Replicates the CONN-06 auto-suggest decision logic from ConnectionForm.svelte lines 83-101.
 * This is a pure extraction of the $effect body so the decision algorithm can be unit tested
 * without mounting the Svelte component.
 *
 * Returns the suggested connection type, or null if no auto-suggest should occur.
 */
function resolveAutoSuggestType(
	sourceId: string,
	targetId: string,
	userHasChangedType: boolean,
	systems: Pick<DiagramSystem, 'id' | 'component_library_id'>[],
	componentLibrary: Pick<ComponentLibraryItem, 'id' | 'is_native_connector'>[],
): 'native_connector' | null {
	if (!sourceId || !targetId) return null;
	if (userHasChangedType) return null;

	const isSourceHub = sourceId === 'hub';
	const isTargetHub = targetId === 'hub';

	if (isSourceHub || isTargetHub) {
		const otherId = isSourceHub ? targetId : sourceId;
		const otherSystem = systems.find((s) => s.id === otherId);
		if (!otherSystem) return null;

		const libItem = componentLibrary.find((c) => c.id === otherSystem.component_library_id);
		if (libItem?.is_native_connector) {
			return 'native_connector';
		}
	}

	return null;
}

describe('suggestions', () => {
	it('returns CRM suggestions for CRM category', () => {
		const suggestions = getSuggestionsForSystem('CRM');
		expect(suggestions).toContain('Customer Data');
		expect(suggestions).toContain('Account Sync');
	});

	it('returns Billing/Payments suggestions for that category', () => {
		const suggestions = getSuggestionsForSystem('Billing/Payments');
		expect(suggestions).toContain('Invoice Data');
	});

	it('returns default suggestions for null category', () => {
		const suggestions = getSuggestionsForSystem(null);
		expect(suggestions).toContain('API Events');
	});

	it('returns default suggestions for unknown category', () => {
		const suggestions = getSuggestionsForSystem('Unknown Category');
		expect(suggestions).toContain('API Events');
	});

	it('has entries for all 10 seed categories', () => {
		const seedCategories = [
			'CRM',
			'Billing/Payments',
			'Finance/ERP',
			'Cloud Marketplace',
			'Analytics',
			'Data Infrastructure',
			'Cloud Providers',
			'Monitoring',
			'Messaging',
			'Developer Tools',
		];
		for (const cat of seedCategories) {
			expect(CATEGORY_SUGGESTIONS[cat]).toBeDefined();
			expect(CATEGORY_SUGGESTIONS[cat].length).toBeGreaterThan(0);
		}
	});
});

describe('HUB_ENDPOINT', () => {
	it('has id "hub" matching nodePositions key', () => {
		expect(HUB_ENDPOINT.id).toBe('hub');
	});

	it('has name "m3ter"', () => {
		expect(HUB_ENDPOINT.name).toBe('m3ter');
	});

	it('has role "hub"', () => {
		expect(HUB_ENDPOINT.role).toBe('hub');
	});
});

describe('CONN-06: auto-suggest native_connector type', () => {
	// Shared fixtures
	const nativeSystem = { id: 'sys-salesforce', component_library_id: 'lib-sf' };
	const nonNativeSystem = { id: 'sys-custom', component_library_id: 'lib-custom' };
	const noLibSystem = { id: 'sys-nolibid', component_library_id: null };

	const systems = [nativeSystem, nonNativeSystem, noLibSystem];

	const componentLibrary = [
		{ id: 'lib-sf', is_native_connector: true },
		{ id: 'lib-custom', is_native_connector: false },
	];

	it('suggests native_connector when source is hub and target is a native connector system', () => {
		const result = resolveAutoSuggestType('hub', 'sys-salesforce', false, systems, componentLibrary);
		expect(result).toBe('native_connector');
	});

	it('suggests native_connector when target is hub and source is a native connector system', () => {
		const result = resolveAutoSuggestType('sys-salesforce', 'hub', false, systems, componentLibrary);
		expect(result).toBe('native_connector');
	});

	it('does not suggest when neither endpoint is the hub', () => {
		const result = resolveAutoSuggestType(
			'sys-salesforce',
			'sys-custom',
			false,
			systems,
			componentLibrary,
		);
		expect(result).toBeNull();
	});

	it('does not suggest when hub is paired with a non-native system', () => {
		const result = resolveAutoSuggestType('hub', 'sys-custom', false, systems, componentLibrary);
		expect(result).toBeNull();
	});

	it('does not suggest when userHasChangedType is true even if hub + native', () => {
		const result = resolveAutoSuggestType('hub', 'sys-salesforce', true, systems, componentLibrary);
		expect(result).toBeNull();
	});

	it('does not suggest when source is empty', () => {
		const result = resolveAutoSuggestType('', 'sys-salesforce', false, systems, componentLibrary);
		expect(result).toBeNull();
	});

	it('does not suggest when target is empty', () => {
		const result = resolveAutoSuggestType('hub', '', false, systems, componentLibrary);
		expect(result).toBeNull();
	});

	it('does not suggest when other system has no component_library_id', () => {
		const result = resolveAutoSuggestType('hub', 'sys-nolibid', false, systems, componentLibrary);
		expect(result).toBeNull();
	});

	it('does not suggest when other system id is not found in systems list', () => {
		const result = resolveAutoSuggestType('hub', 'sys-unknown', false, systems, componentLibrary);
		expect(result).toBeNull();
	});
});
