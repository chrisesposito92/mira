import type { ApiClient } from './api.js';
import type { Workflow, LlmModel, ChatMessageCreate, ChatMessageResponse } from '$lib/types';

export interface WorkflowService {
	list(useCaseId: string): Promise<Workflow[]>;
	get(workflowId: string): Promise<Workflow>;
	start(useCaseId: string, modelId: string): Promise<Workflow>;
	listModels(): Promise<LlmModel[]>;
	listMessages(workflowId: string): Promise<ChatMessageResponse[]>;
	saveMessage(workflowId: string, data: ChatMessageCreate): Promise<ChatMessageResponse>;
}

export function createWorkflowService(client: ApiClient): WorkflowService {
	return {
		list: (useCaseId) => client.get<Workflow[]>(`/api/use-cases/${useCaseId}/workflows`),
		get: (workflowId) => client.get<Workflow>(`/api/workflows/${workflowId}`),
		start: (useCaseId, modelId) =>
			client.post<Workflow>(`/api/use-cases/${useCaseId}/workflows/start`, {
				model_id: modelId,
			}),
		listModels: () => client.get<LlmModel[]>('/api/models'),
		listMessages: (workflowId) =>
			client.get<ChatMessageResponse[]>(`/api/workflows/${workflowId}/messages`),
		saveMessage: (workflowId, data) =>
			client.post<ChatMessageResponse>(`/api/workflows/${workflowId}/messages`, data),
	};
}
