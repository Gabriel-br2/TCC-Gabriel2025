export type Rgb = [number, number, number];

export type ClientConfig = {
  screen: { caption: string; width: number; height: number };
  game: {
    playerNum: number;
    objectsNum: number;
    objectBaseSquareTam: number;
    transparency: number;
  };
  ws: { url: string; port: number };
  player_colors: string[];
  colors: Record<string, Rgb | number[]>;
};

export const DEFAULT_CONFIG: ClientConfig = {
  screen: {
    caption: "Projeto de TCC - Gabriel",
    width: 1200,
    height: 900,
  },
  game: {
    playerNum: 4,
    objectsNum: 2,
    objectBaseSquareTam: 50,
    transparency: 50,
  },
  ws: {
    url: "ws://127.0.0.1:8000",
    port: 8000,
  },
  player_colors: ["blue", "pink", "yellow", "cyan"],
  colors: {
    background: [255, 219, 187],
    blue: [0, 0, 255],
    pink: [255, 0, 155],
    yellow: [255, 255, 0],
    cyan: [0, 255, 255],
    magenta: [255, 0, 255],
    white: [255, 255, 255],
    black: [0, 0, 0],
    red: [255, 0, 0],
    green: [0, 255, 0],
    orange: [255, 165, 0],
    purple: [128, 0, 128],
    brown: [139, 69, 19],
    gray: [128, 128, 128],
    light_gray: [211, 211, 211],
    dark_gray: [64, 64, 64],
    navy: [0, 0, 128],
    teal: [0, 128, 128],
    lime: [50, 205, 50],
    gold: [255, 215, 0],
    beige: [245, 245, 220],
    coral: [255, 127, 80],
    turquoise: [64, 224, 208],
    violet: [238, 130, 238],
    indigo: [75, 0, 130],
  },
};

export async function loadClientConfig(): Promise<ClientConfig> {
  const envWs = import.meta.env.VITE_GAME_WS as string | undefined;
  const fallbackHost =
    typeof location !== "undefined" ? location.hostname : "127.0.0.1";
  try {
    const response = await fetch("/api/public/config");
    if (!response.ok) {
      throw new Error(`config ${response.status}`);
    }
    const remote = (await response.json()) as ClientConfig;
    if (envWs) {
      remote.ws.url = envWs;
    }
    return remote;
  } catch {
    const fallback = structuredClone(DEFAULT_CONFIG);
    fallback.ws.url = envWs ?? `ws://${fallbackHost}:8000`;
    return fallback;
  }
}

export function rgb(colors: ClientConfig["colors"], key: string): Rgb {
  const value = colors[key] ?? [0, 0, 0];
  return [Number(value[0]), Number(value[1]), Number(value[2])];
}
