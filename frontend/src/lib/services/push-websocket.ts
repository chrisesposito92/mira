import { PUBLIC_WS_URL } from '$env/static/public';
import type { PushWsMessage } from '$lib/types';

export class PushWebSocketClient {
	private socket: WebSocket | null = null;

	constructor(
		private onMessage: (msg: PushWsMessage) => void,
		private onClose: () => void,
	) {}

	connect(useCaseId: string, token: string, onOpen?: () => void): void {
		if (this.socket) {
			this.socket.close();
			this.socket = null;
		}

		const wsUrl = PUBLIC_WS_URL || 'ws://localhost:8000';
		const url = `${wsUrl}/ws/push/${useCaseId}?token=${token}`;
		this.socket = new WebSocket(url);

		this.socket.onopen = () => {
			onOpen?.();
		};

		this.socket.onmessage = (event: MessageEvent) => {
			try {
				const msg = JSON.parse(event.data as string) as PushWsMessage;
				this.onMessage(msg);
			} catch {
				// Ignore malformed messages
			}
		};

		this.socket.onclose = () => {
			this.socket = null;
			this.onClose();
		};

		this.socket.onerror = () => {
			// onclose fires after onerror, so close logic is handled there
		};
	}

	send(message: object): void {
		if (this.socket?.readyState === WebSocket.OPEN) {
			this.socket.send(JSON.stringify(message));
		}
	}

	disconnect(): void {
		if (this.socket) {
			this.socket.close();
			this.socket = null;
		}
	}
}
