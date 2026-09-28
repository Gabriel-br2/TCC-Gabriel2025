import type { ClientConfig } from "./config";
import { piecesFromPayload } from "./factory";
import {
  playerKey,
  type BroadcastIn,
  type ObjectsPayload,
  type PiecePose,
  type PlayOut,
} from "./protocol";
import type { Piece } from "./shapes";

export type RemoteState = {
  pieces: Piece[];
  iou: number;
  cycleId: number;
  paused: boolean;
  connectedPlayers: number;
  totalPlayers: number;
  reset: boolean;
  shutdown: boolean;
};

/**
 * Pure broadcast apply matching game/client/application.py::_apply_server_update.
 * Local pieces are never overwritten by a non-reset broadcast.
 * Cycle rebuild relies on `reset:true` (kept sticky by GameSocket if a later
 * reset:false overwrites the latest buffered message before the frame reads it).
 */
export function applyRemoteUpdate(
  state: RemoteState,
  update: BroadcastIn,
  clientId: number,
  config: ClientConfig,
): RemoteState {
  if (update.type === "shutdown") {
    return { ...state, shutdown: true };
  }

  const objects: ObjectsPayload = update.objects ?? {};
  const iou = Number(objects.IoU ?? state.iou);
  const cycleId = Number(objects.cycle_id ?? state.cycleId);
  const paused = Boolean(update.is_paused);
  const connectedPlayers = Number(update.connected_players ?? state.connectedPlayers);
  const totalPlayers = Number(update.total_players ?? config.game.playerNum);
  const cycleAdvanced = cycleId !== state.cycleId;
  // Server may re-broadcast reset:true for a hold window; only rebuild once per cycle.
  const reset = Boolean(update.reset) && cycleAdvanced;

  if (reset) {
    return {
      pieces: piecesFromPayload(objects, clientId, config),
      iou,
      cycleId,
      paused,
      connectedPlayers,
      totalPlayers,
      reset: true,
      shutdown: false,
    };
  }

  const pieces = state.pieces.map((piece) => ({ ...piece }));
  for (const piece of pieces) {
    if (piece.playerId === clientId) {
      continue;
    }
    const key = playerKey(piece.playerId);
    const player = objects[key];
    if (!player || typeof player === "number") {
      continue;
    }
    const pose = player.pos?.[piece.objId];
    if (!pose) {
      continue;
    }
    piece.x = Number(pose[0]);
    piece.y = Number(pose[1]);
    piece.rz = Number(pose[2]);
  }

  return {
    pieces,
    iou,
    cycleId,
    paused,
    connectedPlayers,
    totalPlayers,
    reset: false,
    shutdown: false,
  };
}

export function buildPlayMessage(
  localPieces: Piece[],
  cycleId: number,
  mouse: [number, number],
): PlayOut {
  return {
    pos: localPieces.map(
      (piece) => [piece.x, piece.y, piece.rz, piece.type] as PiecePose,
    ),
    cycle_id: cycleId,
    mouse,
  };
}
