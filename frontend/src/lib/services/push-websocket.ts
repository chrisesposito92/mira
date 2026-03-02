import type { PushWsMessage } from '$lib/types';
import { SimpleWebSocketClient } from './simple-websocket.js';

export class PushWebSocketClient extends SimpleWebSocketClient<PushWsMessage> {
	connect(useCaseId: string, token: string, onOpen?: () => void): void {
		this.connectToPath(`/ws/push/${useCaseId}`, token, onOpen);
	}
}
