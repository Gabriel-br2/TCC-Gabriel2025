import type { ClientConfig } from "./config";
import { pointInPolygon } from "./collision";
import { movePiece, rotatePiece } from "./motion";
import { GameSocket } from "./network";
import type { BroadcastIn } from "./protocol";
import { drawBoard } from "./render";
import { pieceWorldVertices, type Piece } from "./shapes";
import { applyRemoteUpdate, buildPlayMessage } from "./remote";

type ScreenKind = "identify" | "connecting" | "paused" | "playing" | "cycle" | "ended";

export class ClientApp {
  private readonly canvas: HTMLCanvasElement;
  private readonly overlay: HTMLElement;
  private readonly hud: HTMLElement;
  private readonly ctx: CanvasRenderingContext2D;
  private config: ClientConfig;
  private socket: GameSocket | null = null;
  private pieces: Piece[] = [];
  private clientId = -1;
  private cycleId = 0;
  private iou = 0;
  private paused = true;
  private connectedPlayers = 0;
  private totalPlayers = 4;
  private screen: ScreenKind = "identify";
  private running = false;
  private bannerUntil = 0;
  private name = "";
  private connectAttempts = 0;
  private lastPointer: [number, number] = [0, 0];

  constructor(
    canvas: HTMLCanvasElement,
    overlay: HTMLElement,
    hud: HTMLElement,
    config: ClientConfig,
  ) {
    this.canvas = canvas;
    this.overlay = overlay;
    this.hud = hud;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("Canvas 2D not available");
    }
    this.ctx = ctx;
    this.config = config;
    this.resizeCanvas();
    this.bindPointer();
    this.showIdentify();
  }

  private resizeCanvas(): void {
    this.canvas.width = this.config.screen.width;
    this.canvas.height = this.config.screen.height;
  }

  applyConfig(config: ClientConfig): void {
    this.config = config;
    this.resizeCanvas();
  }

  private showIdentify(): void {
    this.screen = "identify";
    this.overlay.hidden = false;
    this.hud.hidden = true;
    this.drawIdleBackground();
    this.overlay.innerHTML = `
      <div class="panel">
        <h1>Identificação do Jogador</h1>
        <label>Nome:
          <input id="field-nome" autocomplete="given-name" />
        </label>
        <label>Sobrenome:
          <input id="field-sobrenome" autocomplete="family-name" />
        </label>
        <button id="btn-continuar" type="button" disabled>Continuar</button>
      </div>
    `;
    const nome = this.overlay.querySelector("#field-nome") as HTMLInputElement;
    const sobrenome = this.overlay.querySelector("#field-sobrenome") as HTMLInputElement;
    const button = this.overlay.querySelector("#btn-continuar") as HTMLButtonElement;
    const sync = () => {
      button.disabled = !(nome.value.trim() && sobrenome.value.trim());
    };
    nome.addEventListener("input", sync);
    sobrenome.addEventListener("input", sync);
    nome.addEventListener("keydown", (event) => {
      if (event.key === "Tab") {
        event.preventDefault();
        sobrenome.focus();
      }
    });
    sobrenome.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !button.disabled) {
        button.click();
      }
    });
    button.addEventListener("click", () => {
      this.name = `${nome.value.trim()} ${sobrenome.value.trim()}`;
      void this.connectLoop();
    });
  }

  private showConnecting(): void {
    this.screen = "connecting";
    this.overlay.hidden = false;
    this.hud.hidden = true;
    const dots = ".".repeat(this.connectAttempts % 4);
    this.overlay.innerHTML = `
      <div class="panel">
        <p class="status">Rodada já completada aguarde sua vez ${dots}</p>
      </div>
    `;
    this.drawIdleBackground();
  }

  private showPause(): void {
    this.screen = "paused";
    this.overlay.hidden = false;
    this.hud.hidden = true;
    this.overlay.innerHTML = `
      <div class="panel">
        <p class="status">Jogo pausado. Aguardando jogadores ${this.connectedPlayers}/${this.totalPlayers}.</p>
        <div class="spinner" aria-hidden="true"></div>
      </div>
    `;
    this.drawIdleBackground();
  }

  private showCycleBanner(): void {
    this.screen = "cycle";
    this.overlay.hidden = false;
    this.hud.hidden = true;
    this.overlay.innerHTML = `
      <div class="panel">
        <p class="status">Objetivo concluído, iniciando próximo ciclo</p>
      </div>
    `;
    this.drawIdleBackground();
  }

  private showEnded(): void {
    this.screen = "ended";
    this.running = false;
    this.overlay.hidden = false;
    this.hud.hidden = true;
    this.overlay.innerHTML = `
      <div class="panel">
        <p class="status">Servidor encerrado.</p>
      </div>
    `;
  }

  private showPlaying(): void {
    this.screen = "playing";
    this.overlay.hidden = true;
    this.overlay.innerHTML = "";
    this.hud.hidden = true;
  }

  private drawIdleBackground(): void {
    drawBoard(this.ctx, this.config, [], 0, { showHud: false });
  }

  private async connectLoop(): Promise<void> {
    this.connectAttempts = 0;
    this.showConnecting();
    const socket = new GameSocket(this.config.ws.url);
    this.socket = socket;
    while (this.screen === "connecting") {
      this.showConnecting();
      try {
        const initial = await socket.connect({ nature: "human", name: this.name });
        this.startSession(initial);
        return;
      } catch {
        this.connectAttempts += 1;
        await sleep(2000);
      }
    }
  }

  private startSession(initial: BroadcastIn): void {
    this.clientId = initial.id ?? -1;
    document.title = `${this.config.screen.caption} - player: ${this.clientId}`;
    this.socket?.setUrgentHandler((update) => {
      this.applyBroadcast(update);
    });
    this.applyBroadcast(initial, true);
    this.running = true;
    requestAnimationFrame((t) => this.frame(t));
  }

  private applyBroadcast(update: BroadcastIn, forceRebuild = false): void {
    if (forceRebuild && update.type !== "shutdown") {
      const forced = { ...update, reset: true };
      const next = applyRemoteUpdate(
        {
          pieces: this.pieces,
          iou: this.iou,
          cycleId: this.cycleId,
          paused: this.paused,
          connectedPlayers: this.connectedPlayers,
          totalPlayers: this.totalPlayers,
          reset: false,
          shutdown: false,
        },
        forced,
        this.clientId,
        this.config,
      );
      this.pieces = next.pieces;
      this.iou = next.iou;
      this.cycleId = next.cycleId;
      this.paused = next.paused;
      this.connectedPlayers = next.connectedPlayers;
      this.totalPlayers = next.totalPlayers;
      return;
    }

    const next = applyRemoteUpdate(
      {
        pieces: this.pieces,
        iou: this.iou,
        cycleId: this.cycleId,
        paused: this.paused,
        connectedPlayers: this.connectedPlayers,
        totalPlayers: this.totalPlayers,
        reset: false,
        shutdown: false,
      },
      update,
      this.clientId,
      this.config,
    );

    if (next.shutdown) {
      this.socket?.close();
      this.showEnded();
      return;
    }

    const prevCycle = this.cycleId;
    this.pieces = next.pieces;
    this.iou = next.iou;
    this.cycleId = next.cycleId;
    this.paused = next.paused;
    this.connectedPlayers = next.connectedPlayers;
    this.totalPlayers = next.totalPlayers;

    if (next.reset) {
      // Only show the 3s banner when entering a new cycle — not on reset re-delivery.
      if (prevCycle !== this.cycleId) {
        this.bannerUntil = performance.now() + 3000;
        this.showCycleBanner();
      }
    }
  }

  private frame(now: number): void {
    if (!this.running) {
      return;
    }
    const incoming = this.socket?.takeState();
    if (incoming) {
      this.applyBroadcast(incoming);
    }
    if (this.socket?.error && this.screen !== "ended") {
      this.showEnded();
      this.overlay.querySelector(".status")?.replaceChildren(
        document.createTextNode("Erro na conexão com o servidor. Encerrando o jogo."),
      );
      return;
    }

    if (this.screen === "cycle") {
      this.drawIdleBackground();
      if (now >= this.bannerUntil) {
        if (this.paused) {
          this.showPause();
        } else {
          this.showPlaying();
        }
      }
      requestAnimationFrame((t) => this.frame(t));
      return;
    }

    if (this.paused) {
      if (this.screen !== "paused") {
        this.showPause();
      } else {
        const status = this.overlay.querySelector(".status");
        if (status) {
          status.textContent = `Jogo pausado. Aguardando jogadores ${this.connectedPlayers}/${this.totalPlayers}.`;
        }
      }
      this.drawIdleBackground();
      requestAnimationFrame((t) => this.frame(t));
      return;
    }

    if (this.screen !== "playing") {
      this.showPlaying();
    }

    drawBoard(this.ctx, this.config, this.pieces, this.iou);
    this.hud.textContent = `Objetivo Concluído: ${(this.iou * 100).toFixed(2)} %`;

    const local = this.pieces.filter((piece) => piece.playerId === this.clientId);
    if (local.length > 0) {
      this.socket?.sendPlay(
        buildPlayMessage(local, this.cycleId, this.lastPointer),
      );
    }

    requestAnimationFrame((t) => this.frame(t));
  }

  private bindPointer(): void {
    this.canvas.addEventListener("contextmenu", (event) => {
      event.preventDefault();
      if (this.screen !== "playing") {
        return;
      }
      const dragging = this.localPieces().find((piece) => piece.dragging);
      if (!dragging) {
        return;
      }
      // Right-click during an active left-drag: some browsers skip pointerdown
      // for button 2 and only emit contextmenu.
      this.lastPointer = this.canvasPoint(event);
      rotatePiece(
        dragging,
        this.localPieces(),
        this.config.screen.width,
        this.config.screen.height,
      );
    });
    this.canvas.addEventListener("pointerdown", (event) => this.onPointerDown(event));
    this.canvas.addEventListener("pointermove", (event) => this.onPointerMove(event));
    this.canvas.addEventListener("pointerup", (event) => this.onPointerUp(event));
    this.canvas.addEventListener("pointerleave", (event) => this.onPointerUp(event));
  }

  private canvasPoint(event: PointerEvent | MouseEvent): [number, number] {
    const rect = this.canvas.getBoundingClientRect();
    const scaleX = this.canvas.width / rect.width;
    const scaleY = this.canvas.height / rect.height;
    return [
      (event.clientX - rect.left) * scaleX,
      (event.clientY - rect.top) * scaleY,
    ];
  }

  private onPointerDown(event: PointerEvent): void {
    if (this.screen !== "playing") {
      return;
    }
    const point = this.canvasPoint(event);
    this.lastPointer = point;
    const local = this.localPieces();

    // While dragging, right-click rotates the grabbed piece (ignore hit-test /
    // grab offset). Keep left-button drag active.
    if (event.button === 2) {
      const dragging = local.find((piece) => piece.dragging);
      if (dragging) {
        rotatePiece(
          dragging,
          local,
          this.config.screen.width,
          this.config.screen.height,
        );
        return;
      }
    }

    for (let i = local.length - 1; i >= 0; i -= 1) {
      const piece = local[i];
      if (!pointInPolygon(point, pieceWorldVertices(piece))) {
        continue;
      }
      if (event.button === 2) {
        rotatePiece(
          piece,
          local,
          this.config.screen.width,
          this.config.screen.height,
        );
      }
      if (event.button === 0) {
        piece.dragging = true;
        piece.offsetX = piece.x - point[0];
        piece.offsetY = piece.y - point[1];
        this.canvas.setPointerCapture(event.pointerId);
      }
      break;
    }
  }

  private onPointerMove(event: PointerEvent): void {
    const point = this.canvasPoint(event);
    this.lastPointer = point;
    if (this.screen !== "playing") {
      return;
    }
    const local = this.localPieces();
    for (const piece of local) {
      if (!piece.dragging) {
        continue;
      }
      const dx = point[0] + piece.offsetX - piece.x;
      const dy = point[1] + piece.offsetY - piece.y;
      movePiece(
        piece,
        dx,
        dy,
        local,
        this.config.screen.width,
        this.config.screen.height,
      );
    }
  }

  private onPointerUp(event: PointerEvent): void {
    if (event.button !== 0 && event.type !== "pointerleave") {
      return;
    }
    for (const piece of this.localPieces()) {
      piece.dragging = false;
    }
  }

  private localPieces(): Piece[] {
    return this.pieces.filter((piece) => piece.playerId === this.clientId);
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
