import type { Point } from "./collision";
import type { ShapeType } from "./protocol";

export type Rgba = [number, number, number, number];

export type Piece = {
  playerId: number;
  objId: number;
  type: ShapeType;
  x: number;
  y: number;
  rz: number;
  color: Rgba;
  vertices: Point[];
  dragging: boolean;
  offsetX: number;
  offsetY: number;
  isRotating: boolean;
};

function sizeFromBase(objectBaseSquareTam: number): number {
  return objectBaseSquareTam / 2;
}

export function verticesFor(type: ShapeType, objectBaseSquareTam: number): Point[] {
  const size = sizeFromBase(objectBaseSquareTam);
  switch (type) {
    case "generic":
      return [
        [-size, -size],
        [-size, size],
        [size, size],
        [size, -size],
      ];
    case "hero":
      return [
        [-3 * size, -size],
        [3 * size, -size],
        [3 * size, size],
        [-3 * size, size],
      ];
    case "ricky":
      return [
        [-3 * size, -size],
        [size, -size],
        [size, -3 * size],
        [3 * size, -3 * size],
        [3 * size, size],
        [-3 * size, size],
      ];
    case "teewee":
      return [
        [-3 * size, -size],
        [3 * size, -size],
        [3 * size, size],
        [size, size],
        [size, 3 * size],
        [-size, 3 * size],
        [-size, size],
        [-3 * size, size],
      ];
    case "z":
      return [
        [-3 * size, -3 * size],
        [size, -3 * size],
        [size, -size],
        [3 * size, -size],
        [3 * size, size],
        [-size, size],
        [-size, -size],
        [-3 * size, -size],
      ];
    default:
      return verticesFor("generic", objectBaseSquareTam);
  }
}

export function transformedVertices(
  vertices: Point[],
  x: number,
  y: number,
  angleDeg: number,
): Point[] {
  const angleRad = (angleDeg * Math.PI) / 180;
  const c = Math.cos(angleRad);
  const s = Math.sin(angleRad);
  return vertices.map(([vx, vy]) => {
    const nx = c * vx + -s * vy + x;
    const ny = s * vx + c * vy + y;
    return [Math.trunc(nx), Math.trunc(ny)];
  });
}

export function pieceWorldVertices(piece: Piece): Point[] {
  return transformedVertices(piece.vertices, piece.x, piece.y, piece.rz);
}

export function createPiece(
  playerId: number,
  objId: number,
  type: ShapeType,
  position: [number, number, number],
  color: Rgba,
  objectBaseSquareTam: number,
): Piece {
  return {
    playerId,
    objId,
    type,
    x: position[0],
    y: position[1],
    rz: position[2],
    color,
    vertices: verticesFor(type, objectBaseSquareTam),
    dragging: false,
    offsetX: 0,
    offsetY: 0,
    isRotating: false,
  };
}

export function tickRotation(piece: Piece): void {
  if (!piece.isRotating) {
    return;
  }
  piece.rz += 10;
  if (piece.rz % 90 === 0) {
    piece.isRotating = false;
  }
}
