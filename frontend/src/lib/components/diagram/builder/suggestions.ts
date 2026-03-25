/** Category-based label suggestions for connection forms (CONN-05, D-12).
 *  Category keys match the seed data in backend/migrations/015_component_library.sql. */
export const CATEGORY_SUGGESTIONS: Record<string, string[]> = {
	CRM: ['Customer Data', 'Account Sync', 'Usage Events'],
	'Billing/Payments': ['Invoice Data', 'Payment Events', 'Subscription Status'],
	'Finance/ERP': ['Financial Data', 'Order Events', 'Revenue Recognition'],
	'Cloud Marketplace': ['Marketplace Listings', 'Usage Reports', 'Revenue Data'],
	Analytics: ['Usage Analytics', 'Billing Reports', 'Revenue Data'],
	'Data Infrastructure': ['Raw Usage Data', 'Billing Records', 'Event Stream'],
	'Cloud Providers': ['Resource Usage', 'Compute Metrics', 'Storage Events'],
	Monitoring: ['Usage Alerts', 'Billing Alerts', 'Threshold Events'],
	Messaging: ['Billing Alerts', 'Usage Alerts', 'Notification Events'],
	'Developer Tools': ['API Events', 'Webhook Data', 'CI/CD Events'],
};

/** Default suggestions when no category match is found. */
const DEFAULT_SUGGESTIONS = ['API Events', 'Webhook Data', 'Custom Integration'];

/**
 * Get label suggestions for a system based on its category.
 * Falls back to default suggestions if category not found.
 */
export function getSuggestionsForSystem(category: string | null): string[] {
	if (!category) return DEFAULT_SUGGESTIONS;
	return CATEGORY_SUGGESTIONS[category] ?? DEFAULT_SUGGESTIONS;
}

/**
 * Synthetic hub endpoint for ConnectionForm dropdowns.
 * The m3ter hub is not in content.systems but must be selectable.
 * Uses 'hub' as ID to match the nodePositions key from the layout algorithm.
 */
export const HUB_ENDPOINT = {
	id: 'hub',
	name: 'm3ter',
	role: 'hub' as const,
};
