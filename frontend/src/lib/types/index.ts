export type EntityType =
	| 'product'
	| 'meter'
	| 'aggregation'
	| 'compound_aggregation'
	| 'plan_template'
	| 'plan'
	| 'pricing'
	| 'account'
	| 'account_plan'
	| 'measurement';

export type ObjectStatus = 'draft' | 'approved' | 'rejected' | 'pushed' | 'push_failed';

export type WorkflowType =
	| 'product_meter_aggregation'
	| 'plan_pricing'
	| 'account_setup'
	| 'usage_submission';

export type WorkflowStatus = 'pending' | 'running' | 'interrupted' | 'completed' | 'failed';

export type UseCaseStatus = 'draft' | 'in_progress' | 'completed';

export type BillingFrequency = 'monthly' | 'quarterly' | 'annually';

export type PricingType = 'per_unit' | 'tiered' | 'volume' | 'stairstep' | 'counter';

export type { UserProfile } from './auth.js';
