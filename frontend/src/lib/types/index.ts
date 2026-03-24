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

export type {
	ConnectionStatus,
	DocumentStatus,
	Project,
	ProjectCreate,
	ProjectUpdate,
	UseCase,
	UseCaseCreate,
	UseCaseUpdate,
	Document,
	OrgConnection,
	OrgConnectionCreate,
	OrgConnectionUpdate,
	OrgConnectionTestResult,
	GeneratedObject,
	GeneratedObjectUpdate,
	BulkStatusUpdate,
	CreateObjectPayload,
} from './api.js';

export type {
	PushWsMessage,
	PushObjectProgress,
	PushSession,
	PushResultResponse,
	BulkPushResultResponse,
	PushStatusResponse,
} from './push.js';

export type { DocProcessingStage, DocWsMessage, DocumentUploadProgress } from './document.js';

export { DOC_PROCESSING_STAGES } from './document.js';

export type { GeneratedUseCase, GeneratorWsMessage, GeneratorClientMessage } from './generator.js';

export type {
	Diagram,
	DiagramListItem,
	DiagramCreate,
	DiagramUpdate,
	DiagramContent,
	DiagramSystem,
	DiagramConnection,
	DiagramSettings,
	ComponentLibraryItem,
} from './diagram.js';

export type {
	LlmModel,
	Workflow,
	EntityItem,
	EntityError,
	EntityDecision,
	ClarificationOption,
	ClarificationQuestion,
	ClarificationAnswer,
	WsStatusMessage,
	WsEntitiesMessage,
	WsClarificationMessage,
	WsCompleteMessage,
	WsErrorMessage,
	WsServerMessage,
	WsResumeMessage,
	WsClarifyMessage,
	WsClientMessage,
	ChatStatusMessage,
	ChatEntitiesMessage,
	ChatClarificationMessage,
	ChatUserDecisionMessage,
	ChatUserClarificationMessage,
	ChatCompleteMessage,
	ChatErrorMessage,
	ChatMessage,
	WsConnectionState,
	ChatMessageCreate,
	ChatMessageResponse,
} from './workflow.js';
