import { loadClientConfig, type ClientConfig } from "../game/config";
import { piecesFromPayload } from "../game/factory";
import type { ObjectsPayload } from "../game/protocol";
import { drawBoard } from "../game/render";
import "./style.css";

type Slot = {
  id: number;
  color: string | null;
  connected: boolean;
  nature: string | null;
  name_masked: string | null;
  name: string | null;
};

type Status = {
  cycle_id: number;
  iou: number;
  is_paused: boolean;
  connected_players: number;
  total_players: number;
  goal_area: number;
  slots: Slot[];
  objects: ObjectsPayload;
};

type LogIndex = { sessions: { id: string; files: string[] }[] };

const TOKEN_KEY = "tcc-admin-token";
const rootNode = document.querySelector<HTMLElement>("#admin-root");
if (!rootNode) {
  throw new Error("Missing admin root");
}
const root = rootNode;

let token = sessionStorage.getItem(TOKEN_KEY) ?? "";
let reveal = false;
let configDump: unknown = null;
let clientConfig: ClientConfig;

void startAdmin();

async function startAdmin(): Promise<void> {
  clientConfig = await loadClientConfig();

  root.innerHTML = `
  <header>
    <div>
      <h1>Painel do experimento</h1>
      <p class="sub">Operador apenas. O socket do jogo permanece sem autenticação e sem comandos admin.</p>
    </div>
    <form id="auth-form">
      <label>Token
        <input id="token" type="password" autocomplete="current-password" />
      </label>
      <button type="submit">Entrar</button>
    </form>
  </header>
  <p id="auth-error" class="error" hidden></p>
  <section id="dashboard" hidden>
    <div class="metrics">
      <article><span>Ciclo</span><strong id="m-cycle">—</strong></article>
      <article><span>IoU</span><strong id="m-iou">—</strong></article>
      <article><span>Jogadores</span><strong id="m-players">—</strong></article>
      <article><span>Estado</span><strong id="m-paused">—</strong></article>
    </div>
    <div class="toolbar">
      <label class="check">
        <input id="reveal" type="checkbox" />
        Revelar nomes
      </label>
      <button id="btn-shutdown" type="button" class="danger">Encerrar sessão</button>
    </div>
    <div class="grid">
      <div>
        <h2>Slots</h2>
        <table>
          <thead>
            <tr>
              <th>Slot</th>
              <th>Cor</th>
              <th>Natureza</th>
              <th>Conectado</th>
              <th>Nome</th>
            </tr>
          </thead>
          <tbody id="slots"></tbody>
        </table>
      </div>
      <div>
        <h2>Espectador</h2>
        <canvas id="spectator"></canvas>
      </div>
    </div>
    <div class="grid">
      <div>
        <h2>Configuração (somente leitura)</h2>
        <pre id="config-view">carregando…</pre>
      </div>
      <div>
        <h2>Logs</h2>
        <div id="logs"></div>
      </div>
    </div>
  </section>
`;

const tokenInput = root.querySelector<HTMLInputElement>("#token")!;
const authForm = root.querySelector<HTMLFormElement>("#auth-form")!;
const authError = root.querySelector<HTMLElement>("#auth-error")!;
const dashboard = root.querySelector<HTMLElement>("#dashboard")!;
const revealBox = root.querySelector<HTMLInputElement>("#reveal")!;
const shutdownBtn = root.querySelector<HTMLButtonElement>("#btn-shutdown")!;
const slotsBody = root.querySelector<HTMLElement>("#slots")!;
const logsEl = root.querySelector<HTMLElement>("#logs")!;
const configView = root.querySelector<HTMLElement>("#config-view")!;
const spectator = root.querySelector<HTMLCanvasElement>("#spectator")!;
const specCtx = spectator.getContext("2d");

tokenInput.value = token;
spectator.width = clientConfig.screen.width;
spectator.height = clientConfig.screen.height;

authForm.addEventListener("submit", (event) => {
  event.preventDefault();
  token = tokenInput.value.trim();
  sessionStorage.setItem(TOKEN_KEY, token);
  void bootstrap();
});

revealBox.addEventListener("change", () => {
  reveal = revealBox.checked;
  void refreshStatus();
});

shutdownBtn.addEventListener("click", () => {
  if (!window.confirm("Enviar shutdown para todos os clientes de jogo?")) {
    return;
  }
  void shutdown();
});

async function api(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  return fetch(path, { ...init, headers });
}

function showAuthError(message: string): void {
  authError.hidden = false;
  authError.textContent = message;
  dashboard.hidden = true;
}

async function bootstrap(): Promise<void> {
  if (!token) {
    showAuthError("Informe o token de administrador (ADMIN_TOKEN).");
    return;
  }
  const statusRes = await api(`/api/admin/status?reveal=${reveal ? 1 : 0}`);
  if (statusRes.status === 401) {
    showAuthError("Token inválido.");
    return;
  }
  if (!statusRes.ok) {
    showAuthError(`Falha ao ler status (${statusRes.status}).`);
    return;
  }
  authError.hidden = true;
  dashboard.hidden = false;
  const status = (await statusRes.json()) as Status;
  renderStatus(status);
  await Promise.all([loadConfig(), loadLogs()]);
}

async function refreshStatus(): Promise<void> {
  if (dashboard.hidden) {
    return;
  }
  const response = await api(`/api/admin/status?reveal=${reveal ? 1 : 0}`);
  if (response.status === 401) {
    showAuthError("Token inválido.");
    return;
  }
  if (!response.ok) {
    return;
  }
  renderStatus((await response.json()) as Status);
}

function renderStatus(status: Status): void {
  root.querySelector("#m-cycle")!.textContent = String(status.cycle_id);
  root.querySelector("#m-iou")!.textContent = `${(status.iou * 100).toFixed(2)} %`;
  root.querySelector("#m-players")!.textContent =
    `${status.connected_players}/${status.total_players}`;
  root.querySelector("#m-paused")!.textContent = status.is_paused ? "pausado" : "em jogo";

  slotsBody.innerHTML = status.slots
    .map((slot) => {
      const name = reveal ? slot.name ?? "—" : slot.name_masked ?? "—";
      return `<tr>
        <td>P${slot.id}</td>
        <td><span class="swatch" style="background:${slot.color ?? "#444"}"></span> ${slot.color ?? "—"}</td>
        <td>${slot.nature ?? "—"}</td>
        <td>${slot.connected ? "sim" : "não"}</td>
        <td>${escapeHtml(name)}</td>
      </tr>`;
    })
    .join("");

  if (specCtx) {
    const spectatorConfig: ClientConfig = {
      ...clientConfig,
      game: { ...clientConfig.game, transparency: 200 },
    };
    const pieces = piecesFromPayload(status.objects ?? {}, -1, spectatorConfig);
    const mice: { color: string; x: number; y: number }[] = [];
    for (const [key, value] of Object.entries(status.objects ?? {})) {
      if (key === "IoU" || key === "cycle_id" || !value || typeof value === "number") {
        continue;
      }
      const mouse = value.mouse;
      if (mouse && mouse.length >= 2) {
        mice.push({
          color: value.color,
          x: Number(mouse[0]),
          y: Number(mouse[1]),
        });
      }
    }
    drawBoard(specCtx, spectatorConfig, pieces, status.iou, {
      showHud: true,
      showMice: mice,
    });
  }
}

async function loadConfig(): Promise<void> {
  const response = await api("/api/admin/config");
  if (!response.ok) {
    configView.textContent = "Não foi possível carregar a configuração.";
    return;
  }
  configDump = await response.json();
  configView.textContent = JSON.stringify(configDump, null, 2);
}

async function loadLogs(): Promise<void> {
  const response = await api("/api/admin/logs");
  if (!response.ok) {
    logsEl.textContent = "Não foi possível listar os logs.";
    return;
  }
  const data = (await response.json()) as LogIndex;
  if (!data.sessions.length) {
    logsEl.innerHTML = "<p>Nenhuma sessão em LOGS/.</p>";
    return;
  }
  logsEl.innerHTML = data.sessions
    .map((session) => {
      const links = session.files
        .map(
          (file) =>
            `<button type="button" data-session="${session.id}" data-file="${file}">${file}</button>`,
        )
        .join(" ");
      return `<article class="log-session"><h3>${session.id}</h3><div>${links}</div></article>`;
    })
    .join("");
  logsEl.querySelectorAll<HTMLButtonElement>("button[data-file]").forEach((button) => {
    button.addEventListener("click", () => {
      void downloadLog(button.dataset.session ?? "", button.dataset.file ?? "");
    });
  });
}

async function downloadLog(session: string, filename: string): Promise<void> {
  const response = await api(`/api/admin/logs/${encodeURIComponent(session)}/${encodeURIComponent(filename)}`);
  if (!response.ok) {
    window.alert("Falha ao baixar o log.");
    return;
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${session}-${filename}`;
  link.click();
  URL.revokeObjectURL(url);
}

async function shutdown(): Promise<void> {
  const response = await api("/api/admin/shutdown", { method: "POST" });
  if (!response.ok) {
    window.alert("Falha ao encerrar a sessão.");
    return;
  }
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

if (token) {
  void bootstrap();
}

window.setInterval(() => {
  void refreshStatus();
}, 250);
}
