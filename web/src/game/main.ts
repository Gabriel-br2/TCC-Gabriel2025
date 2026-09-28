import { loadClientConfig } from "./config";
import { ClientApp } from "./app";
import "./style.css";

async function boot(): Promise<void> {
  const canvas = document.querySelector<HTMLCanvasElement>("#board");
  const overlay = document.querySelector<HTMLElement>("#overlay");
  const hud = document.querySelector<HTMLElement>("#hud");
  if (!canvas || !overlay || !hud) {
    throw new Error("Missing game DOM nodes");
  }
  const config = await loadClientConfig();
  new ClientApp(canvas, overlay, hud, config);
}

void boot();
