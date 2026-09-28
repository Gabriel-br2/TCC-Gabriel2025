import { pieceWorldVertices, transformedVertices, type Piece } from "./shapes";
import { polygonsIntersect } from "./collision";

/** Match game/client/players/motion.py::get_interpolation (steps from max abs). */
export function interpolate(dx: number, dy: number): { xs: number[]; ys: number[] } {
  const steps = Math.trunc(Math.max(Math.abs(dx), Math.abs(dy)));
  if (steps === 0) {
    return { xs: [], ys: [] };
  }
  const xs: number[] = [];
  const ys: number[] = [];
  for (let i = 1; i <= steps; i += 1) {
    xs.push(Math.round((dx * i) / steps));
    ys.push(Math.round((dy * i) / steps));
  }
  return { xs, ys };
}

function inBounds(
  vertices: [number, number][],
  width: number,
  height: number,
): boolean {
  return vertices.every(
    ([x, y]) => x >= 0 && x <= width && y >= 0 && y <= height,
  );
}

function collidesWithSiblings(
  piece: Piece,
  world: [number, number][],
  siblings: Piece[],
): boolean {
  for (const other of siblings) {
    if (other === piece) {
      continue;
    }
    if (polygonsIntersect(world, pieceWorldVertices(other))) {
      return true;
    }
  }
  return false;
}

export function movePiece(
  piece: Piece,
  dx: number,
  dy: number,
  siblings: Piece[],
  width: number,
  height: number,
): boolean {
  const startX = piece.x;
  const startY = piece.y;
  const { xs, ys } = interpolate(dx, dy);
  if (xs.length === 0) {
    return true;
  }

  for (let i = 0; i < xs.length; i += 1) {
    const newX = startX + xs[i];
    const newY = startY + ys[i];
    const world = transformedVertices(piece.vertices, newX, newY, piece.rz);
    if (!inBounds(world, width, height)) {
      return false;
    }
    if (collidesWithSiblings(piece, world, siblings)) {
      return false;
    }
    piece.x = Math.trunc(newX);
    piece.y = Math.trunc(newY);
  }
  return true;
}

export function rotatePiece(
  piece: Piece,
  siblings: Piece[],
  width: number,
  height: number,
): boolean {
  if (piece.isRotating) {
    return false;
  }
  const world = transformedVertices(
    piece.vertices,
    piece.x,
    piece.y,
    piece.rz + 90,
  );
  if (!inBounds(world, width, height)) {
    return false;
  }
  if (collidesWithSiblings(piece, world, siblings)) {
    return false;
  }
  piece.isRotating = true;
  return true;
}
