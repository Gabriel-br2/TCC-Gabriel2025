import { rgb, type ClientConfig } from "./config";
import {
  NON_PLAYER_KEYS,
  playerKey,
  type ObjectsPayload,
  type PlayerPayload,
  type ShapeType,
} from "./protocol";
import { createPiece, type Piece } from "./shapes";

export { playerKey };

export function piecesFromPayload(
  objects: ObjectsPayload,
  clientId: number,
  config: ClientConfig,
): Piece[] {
  const pieces: Piece[] = [];
  for (const [key, value] of Object.entries(objects)) {
    if (NON_PLAYER_KEYS.has(key) || !value || typeof value === "number") {
      continue;
    }
    const player = value as PlayerPayload;
    const playerId = Number(player.id ?? key.slice(1));
    const alpha = playerId === clientId ? 255 : config.game.transparency;
    const colorRgb = rgb(config.colors, player.color);
    const color: [number, number, number, number] = [
      colorRgb[0],
      colorRgb[1],
      colorRgb[2],
      alpha,
    ];
    player.pos.forEach((pose, objId) => {
      const type = pose[3] as ShapeType;
      pieces.push(
        createPiece(
          playerId,
          objId,
          type,
          [Number(pose[0]), Number(pose[1]), Number(pose[2])],
          color,
          config.game.objectBaseSquareTam,
        ),
      );
    });
  }
  pieces.sort((a, b) => {
    const aLocal = a.playerId === clientId ? 0 : 1;
    const bLocal = b.playerId === clientId ? 0 : 1;
    if (aLocal !== bLocal) {
      return aLocal - bLocal;
    }
    if (a.playerId !== b.playerId) {
      return a.playerId - b.playerId;
    }
    return a.objId - b.objId;
  });
  return pieces;
}
