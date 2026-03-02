import type { DocWsMessage } from '$lib/types';
import { SimpleWebSocketClient } from './simple-websocket.js';

export class DocWebSocketClient extends SimpleWebSocketClient<DocWsMessage> {
	connect(projectId: string, token: string, onOpen?: () => void): void {
		this.connectToPath(`/ws/documents/${projectId}`, token, onOpen);
	}
}
