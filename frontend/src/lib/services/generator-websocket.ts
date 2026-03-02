import { SimpleWebSocketClient } from './simple-websocket.js';
import type { GeneratorWsMessage } from '$lib/types/generator.js';

export class GeneratorWebSocketClient extends SimpleWebSocketClient<GeneratorWsMessage> {
	connect(projectId: string, token: string, onOpen?: () => void): void {
		this.connectToPath(`/ws/generate/${projectId}`, token, onOpen);
	}
}
