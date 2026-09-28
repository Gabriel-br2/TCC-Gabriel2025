/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GAME_WS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module "*.css";

