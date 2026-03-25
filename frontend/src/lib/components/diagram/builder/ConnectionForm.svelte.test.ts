import { describe, it, expect } from 'vitest';
import { getSuggestionsForSystem, CATEGORY_SUGGESTIONS, HUB_ENDPOINT } from './suggestions.js';

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
