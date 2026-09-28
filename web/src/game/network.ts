import type { BroadcastIn, HandshakeOut, PlayOut } from "./protocol";

const CONNECT_TIMEOUT_MS = 2000;
const HANDSHAKE_TIMEOUT_MS = 10000;

export class GameSocket {
  url: string;
  private ws: WebSocket | null = null;
  private latest: BroadcastIn | null = null;
  /** Survives reset:false overwrites until the game loop/urgent handler consumes it. */
  private pendingReset = false;
  private onUrgent: ((update: BroadcastIn) => void) | null = null;
  error: string | null = null;
  clientId: number | null = null;
  timestamp: string | null = null;

  constructor(url: string) {
    this.url = url;
  }

  /** Called immediately when a cycle reset is received (does not wait for rAF). */
  setUrgentHandler(handler: ((update: BroadcastIn) => void) | null): void {
    this.onUrgent = handler;
  }

  async connect(identity: HandshakeOut): Promise<BroadcastIn> {
    this.error = null;
    this.latest = null;
    this.pendingReset = false;
    const ws = await this.openSocket();
    this.ws = ws;
    ws.send(JSON.stringify(identity));

    const deadline = Date.now() + HANDSHAKE_TIMEOUT_MS;
    while (Date.now() < deadline) {
      const remaining = deadline - Date.now();
      const message = await this.waitMessage(ws, remaining);
      if (message && typeof message.id === "number") {
        this.clientId = message.id;
        this.timestamp = message.timestamp ?? null;
        ws.onmessage = (event) => this.onMessage(event);
        ws.onclose = () => {
          this.error = "disconnected";
        };
        ws.onerror = () => {
          this.error = "disconnected";
        };
        return message;
      }
    }
    ws.close();
    throw new Error("Handshake incompleto: nenhuma resposta com 'id'.");
  }

  takeState(): BroadcastIn | null {
    const state = this.latest;
    this.latest = null;
    if (!state) {
      return null;
    }
    if (this.pendingReset) {
      this.pendingReset = false;
      return { ...state, reset: true };
    }
    return state;
  }

  sendPlay(payload: PlayOut): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }
    this.ws.send(JSON.stringify(payload));
  }

  close(): void {
    this.onUrgent = null;
    this.ws?.close();
    this.ws = null;
  }

  private onMessage(event: MessageEvent): void {
    try {
      const update = JSON.parse(String(event.data)) as BroadcastIn;
      const sawReset = Boolean(update.reset);
      if (sawReset) {
        this.pendingReset = true;
      }
      this.latest = update;
      // Flush reset immediately so background tabs (throttled rAF) still advance.
      if (sawReset && this.onUrgent) {
        const state = this.takeState();
        if (state) {
          this.onUrgent(state);
        }
      }
    } catch {
      /* ignore malformed frames */
    }
  }

  private openSocket(): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      const ngrok = this.url.includes("ngrok");
      const url = ngrok && !this.url.includes("ngrok-skip-browser-warning")
        ? `${this.url}${this.url.includes("?") ? "&" : "?"}ngrok-skip-browser-warning=1`
        : this.url;
      const ws = new WebSocket(url);
      const timer = window.setTimeout(() => {
        ws.close();
        reject(new Error("connect timeout"));
      }, CONNECT_TIMEOUT_MS);
      ws.onopen = () => {
        window.clearTimeout(timer);
        resolve(ws);
      };
      ws.onerror = () => {
        window.clearTimeout(timer);
        reject(new Error("connect failed"));
      };
    });
  }

  private waitMessage(ws: WebSocket, timeoutMs: number): Promise<BroadcastIn | null> {
    return new Promise((resolve) => {
      const timer = window.setTimeout(() => {
        cleanup();
        resolve(null);
      }, timeoutMs);
      const onMessage = (event: MessageEvent) => {
        cleanup();
        try {
          resolve(JSON.parse(String(event.data)) as BroadcastIn);
        } catch {
          resolve(null);
        }
      };
      const onClose = () => {
        cleanup();
        resolve(null);
      };
      const cleanup = () => {
        window.clearTimeout(timer);
        ws.removeEventListener("message", onMessage);
        ws.removeEventListener("close", onClose);
      };
      ws.addEventListener("message", onMessage);
      ws.addEventListener("close", onClose);
    });
  }
}
