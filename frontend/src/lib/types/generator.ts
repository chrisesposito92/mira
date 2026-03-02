import type { ClarificationAnswer } from './workflow.js';

export interface GeneratedUseCase {
	title: string;
	description: string;
	billing_frequency: 'monthly' | 'quarterly' | 'annually' | null;
	currency: string;
	target_billing_model: string | null;
	notes: string | null;
}

/** Generator clarification option (backend sends label + description, no id). */
export interface GeneratorClarificationOption {
	label: string;
	description?: string;
}

/** Generator clarification question (no id or allows_free_text — simpler than workflow questions). */
export interface GeneratorClarificationQuestion {
	question: string;
	options: GeneratorClarificationOption[];
	recommendation?: string;
}

export type GeneratorWsMessage =
	| { type: 'gen_status'; step: string; message: string }
	| { type: 'gen_clarification'; questions: GeneratorClarificationQuestion[] }
	| { type: 'gen_use_cases'; use_cases: GeneratedUseCase[] }
	| { type: 'gen_error'; message: string };

export type GeneratorClientMessage =
	| {
			type: 'start_generate';
			customer_name: string;
			num_use_cases: number;
			notes?: string;
			attachment_text?: string;
			model_id: string;
	  }
	| { type: 'clarify'; answers: ClarificationAnswer[] };
