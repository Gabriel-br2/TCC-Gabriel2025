export type ShapeType = "generic" | "hero" | "ricky" | "teewee" | "z";

export type PiecePose = [number, number, number, ShapeType];

export type PlayerPayload = {
  id?: number;
  color: string;
  pos: PiecePose[];
  mouse?: [number, number] | number[] | null;
};

export type ObjectsPayload = {
  IoU?: number;
  cycle_id?: number;
  [playerKey: string]: PlayerPayload | number | undefined;
};

export type HandshakeOut = {
  nature: "human" | "LLM";
  name: string;
};

export type BroadcastIn = {
  type?: string;
  id?: number;
  timestamp?: string;
  objects?: ObjectsPayload;
  reset?: boolean;
  is_paused?: boolean;
  connected_players?: number;
  total_players?: number;
};

export type PlayOut = {
  pos: PiecePose[];
  cycle_id: number;
  mouse: [number, number];
};

export function playerKey(playerId: number): string {
  return `P${playerId}`;
}

export const NON_PLAYER_KEYS = new Set(["IoU", "cycle_id"]);
