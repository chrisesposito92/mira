import { PUBLIC_WS_URL } from '$env/static/public';
import type { WsServerMessage, WsClientMessage, WsConnectionState } from '$lib/types';

const INITIAL_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 30000;
const MAX_RECONNECT_ATTEMPTS = 5;

export class WebSocketClient {
	private socket: WebSocket | null = null;
	private reconnectAttempts = 0;
	private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
	private intentionalClose = false;
	private currentWorkflowId: string | null = null;
	private currentToken: string | null = null;

	constructor(
		private onMessage: (msg: WsServerMessage) => void,
		private onStateChange: (state: WsConnectionState) => void,
	) {}

	connect(workflowId: string, token: string): void {
		this.intentionalClose = false;
		this.currentWorkflowId = workflowId;
		this.currentToken = token;
		this.reconnectAttempts = 0;
		this.openSocket();
	}

	send(message: WsClientMessage): void {
		if (this.socket?.readyState === WebSocket.OPEN) {
			this.socket.send(JSON.stringify(message));
		}
	}

	disconnect(): void {
		this.intentionalClose = true;
		this.clearReconnectTimer();
		if (this.socket) {
			this.socket.close();
			this.socket = null;
		}
		this.onStateChange('disconnected');
	}

	private openSocket(): void {
		if (this.socket) {
			this.socket.close();
			this.socket = null;
		}

		const isReconnect = this.reconnectAttempts > 0;
		this.onStateChange(isReconnect ? 'reconnecting' : 'connecting');

		const wsUrl = PUBLIC_WS_URL || 'ws://localhost:8000';
		const url = `${wsUrl}/ws/workflows/${this.currentWorkflowId}?token=${this.currentToken}`;
		this.socket = new WebSocket(url);

		this.socket.onopen = () => {
			this.reconnectAttempts = 0;
			this.onStateChange('connected');
		};

		this.socket.onmessage = (event: MessageEvent) => {
			try {
				const msg = JSON.parse(event.data as string) as WsServerMessage;
				this.onMessage(msg);
			} catch {
				// Ignore malformed messages
			}
		};

		this.socket.onclose = () => {
			this.socket = null;
			if (!this.intentionalClose) {
				this.scheduleReconnect();
			} else {
				this.onStateChange('disconnected');
			}
		};

		this.socket.onerror = () => {
			// onclose fires after onerror, so reconnect logic is handled there
		};
	}

	private scheduleReconnect(): void {
		if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
			this.onStateChange('disconnected');
			return;
		}

		this.onStateChange('reconnecting');
		const delay = Math.min(
			INITIAL_RECONNECT_DELAY * Math.pow(2, this.reconnectAttempts),
			MAX_RECONNECT_DELAY,
		);
		this.reconnectAttempts++;

		this.reconnectTimer = setTimeout(() => {
			this.reconnectTimer = null;
			this.openSocket();
		}, delay);
	}

	private clearReconnectTimer(): void {
		if (this.reconnectTimer !== null) {
			clearTimeout(this.reconnectTimer);
			this.reconnectTimer = null;
		}
	}
}
