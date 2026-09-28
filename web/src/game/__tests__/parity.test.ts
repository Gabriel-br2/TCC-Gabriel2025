import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { pointInPolygon } from "../collision";
import { DEFAULT_CONFIG, type ClientConfig } from "../config";
import { piecesFromPayload } from "../factory";
import { interpolate, movePiece, rotatePiece } from "../motion";
import { NON_PLAYER_KEYS, playerKey, type ShapeType } from "../protocol";
import { applyRemoteUpdate, buildPlayMessage } from "../remote";
import {
  createPiece,
  tickRotation,
  transformedVertices,
  verticesFor,
  type Piece,
} from "../shapes";

const root = dirname(fileURLToPath(import.meta.url));
const goldenPath = resolve(root, "../../../../tests/fixtures/parity_golden.json");
const golden = JSON.parse(readFileSync(goldenPath, "utf-8")) as Golden;

type Golden = {
  meta: {
    player_key_example: string;
    non_player_keys: string[];
    objectBaseSquareTam: number;
    screen: { width: number; height: number };
  };
  vertices: Record<string, [number, number][]>;
  transforms: {
    type: ShapeType;
    x: number;
    y: number;
    rz: number;
    world: [number, number][];
  }[];
  hit_tests: {
    point: [number, number];
    polygon: [number, number][];
    inside: boolean;
  }[];
  interpolation: {
    dx: number;
    dy: number;
    steps: number;
    xs: number[];
    ys: number[];
  }[];
  moves: {
    name: string;
    start: [number, number, number, ShapeType];
    sibling: [number, number, number, ShapeType] | null;
    dx: number;
    dy: number;
    ok: boolean;
    end: [number, number, number];
  }[];
  rotates: {
    name: string;
    start: [number, number, number, ShapeType];
    sibling: [number, number, number, ShapeType] | null;
    ok: boolean;
    isRotating: boolean;
  }[];
  payload: {
    clientId: number;
    objects: Record<string, unknown>;
    transparency: number;
    pieces: {
      playerId: number;
      objId: number;
      type: ShapeType;
      x: number;
      y: number;
      rz: number;
      alpha: number;
      vertices: [number, number][];
    }[];
    draw_order: [number, number][];
  };
  remote_updates: {
    name: string;
    clientId: number;
    before: {
      playerId: number;
      objId: number;
      x: number;
      y: number;
      rz: number;
      type: ShapeType;
    }[];
    update: Record<string, unknown>;
    after: { playerId: number; objId: number; x: number; y: number; rz: number }[];
    iou: number;
    cycle_id: number;
  }[];
  play_message: {
    pos: [number, number, number, ShapeType][];
    cycle_id: number;
    mouse: [number, number];
  };
  ui_copy: {
    cycle_ms: number;
    hud: string;
  };
};

function pieceFromPose(
  pose: [number, number, number, ShapeType],
  playerId = 0,
  objId = 0,
): Piece {
  return createPiece(
    playerId,
    objId,
    pose[3],
    [pose[0], pose[1], pose[2]],
    [0, 0, 255, 255],
    golden.meta.objectBaseSquareTam,
  );
}

function testConfig(): ClientConfig {
  return structuredClone(DEFAULT_CONFIG);
}

describe("web client parity with Pygame golden fixtures", () => {
  it("matches protocol helpers", () => {
    expect(playerKey(2)).toBe(golden.meta.player_key_example);
    expect([...NON_PLAYER_KEYS].sort()).toEqual(
      [...golden.meta.non_player_keys].sort(),
    );
  });

  it("matches shape local vertices", () => {
    for (const [type, expected] of Object.entries(golden.vertices)) {
      expect(verticesFor(type as ShapeType, golden.meta.objectBaseSquareTam)).toEqual(
        expected,
      );
    }
  });

  it("matches world transforms (int truncation)", () => {
    for (const case_ of golden.transforms) {
      const local = verticesFor(case_.type, golden.meta.objectBaseSquareTam);
      expect(transformedVertices(local, case_.x, case_.y, case_.rz)).toEqual(
        case_.world,
      );
    }
  });

  it("matches point-in-polygon hit tests", () => {
    for (const case_ of golden.hit_tests) {
      expect(pointInPolygon(case_.point, case_.polygon)).toBe(case_.inside);
    }
  });

  it("matches move interpolation steps", () => {
    for (const case_ of golden.interpolation) {
      const { xs, ys } = interpolate(case_.dx, case_.dy);
      expect(xs).toEqual(case_.xs);
      expect(ys).toEqual(case_.ys);
      expect(xs.length).toBe(case_.steps);
    }
  });

  it("matches move outcomes (bounds + sibling collision)", () => {
    const { width, height } = golden.meta.screen;
    for (const case_ of golden.moves) {
      const a = pieceFromPose(case_.start, 0, 0);
      const siblings = [a];
      if (case_.sibling) {
        siblings.push(pieceFromPose(case_.sibling, 0, 1));
      }
      const ok = movePiece(a, case_.dx, case_.dy, siblings, width, height);
      expect(ok, case_.name).toBe(case_.ok);
      expect([a.x, a.y, a.rz], case_.name).toEqual(case_.end);
    }
  });

  it("matches rotate outcomes", () => {
    const { width, height } = golden.meta.screen;
    for (const case_ of golden.rotates) {
      const a = pieceFromPose(case_.start, 0, 0);
      const siblings = [a];
      if (case_.sibling) {
        siblings.push(pieceFromPose(case_.sibling, 0, 1));
      }
      const ok = rotatePiece(a, siblings, width, height);
      expect(ok, case_.name).toBe(case_.ok);
      expect(a.isRotating, case_.name).toBe(case_.isRotating);
    }
  });

  it("matches payload parsing / draw order / alpha", () => {
    const config = testConfig();
    config.game.transparency = golden.payload.transparency;
    const pieces = piecesFromPayload(
      golden.payload.objects as never,
      golden.payload.clientId,
      config,
    );
    expect(pieces.map((p) => [p.playerId, p.objId])).toEqual(
      golden.payload.draw_order,
    );
    for (let i = 0; i < pieces.length; i += 1) {
      const piece = pieces[i];
      const expected = golden.payload.pieces[i];
      expect(piece.playerId).toBe(expected.playerId);
      expect(piece.objId).toBe(expected.objId);
      expect(piece.type).toBe(expected.type);
      expect(piece.x).toBe(expected.x);
      expect(piece.y).toBe(expected.y);
      expect(piece.rz).toBe(expected.rz);
      expect(piece.color[3]).toBe(expected.alpha);
      expect(piece.vertices).toEqual(expected.vertices);
    }
  });

  it("matches remote update semantics (never overwrite local)", () => {
    const config = testConfig();
    for (const case_ of golden.remote_updates) {
      const pieces = case_.before.map((p) =>
        createPiece(
          p.playerId,
          p.objId,
          p.type,
          [p.x, p.y, p.rz],
          [0, 0, 255, 255],
          config.game.objectBaseSquareTam,
        ),
      );
      const next = applyRemoteUpdate(
        {
          pieces,
          iou: 0,
          cycleId: 0,
          paused: false,
          connectedPlayers: 4,
          totalPlayers: 4,
          reset: false,
          shutdown: false,
        },
        case_.update as never,
        case_.clientId,
        config,
      );
      expect(
        next.pieces.map((p) => ({
          playerId: p.playerId,
          objId: p.objId,
          x: p.x,
          y: p.y,
          rz: p.rz,
        })),
        case_.name,
      ).toEqual(case_.after);
      expect(next.iou).toBe(case_.iou);
      expect(next.cycleId).toBe(case_.cycle_id);
    }
  });

  it("builds play messages with pos separate from mouse", () => {
    const local = golden.play_message.pos.map((pose, i) =>
      pieceFromPose(pose, 0, i),
    );
    const msg = buildPlayMessage(
      local,
      golden.play_message.cycle_id,
      golden.play_message.mouse,
    );
    expect(msg).toEqual(golden.play_message);
    expect(Object.keys(msg).sort()).toEqual(["cycle_id", "mouse", "pos"]);
    expect(msg.pos.every((p) => p.length === 4)).toBe(true);
  });
});

describe("rotation animation and broadcast edge cases", () => {
  it("advances +10 until multiple of 90", () => {
    const piece = createPiece(
      0,
      0,
      "generic",
      [400, 400, 0],
      [0, 0, 255, 255],
      50,
    );
    piece.isRotating = true;
    while (piece.isRotating) {
      tickRotation(piece);
    }
    expect(piece.rz).toBe(90);
  });

  it("handles shutdown broadcast", () => {
    const config = testConfig();
    const next = applyRemoteUpdate(
      {
        pieces: [],
        iou: 0.2,
        cycleId: 1,
        paused: false,
        connectedPlayers: 4,
        totalPlayers: 4,
        reset: false,
        shutdown: false,
      },
      { type: "shutdown" },
      0,
      config,
    );
    expect(next.shutdown).toBe(true);
    expect(next.iou).toBe(0.2);
  });

  it("rebuilds all pieces on reset", () => {
    const config = testConfig();
    config.game.transparency = golden.payload.transparency;
    const next = applyRemoteUpdate(
      {
        pieces: [
          createPiece(0, 0, "generic", [1, 1, 0], [0, 0, 255, 255], 50),
        ],
        iou: 0.9,
        cycleId: 1,
        paused: false,
        connectedPlayers: 4,
        totalPlayers: 4,
        reset: false,
        shutdown: false,
      },
      {
        reset: true,
        is_paused: false,
        connected_players: 4,
        total_players: 4,
        objects: golden.payload.objects as never,
      },
      golden.payload.clientId,
      config,
    );
    expect(next.reset).toBe(true);
    expect(next.pieces.length).toBe(golden.payload.pieces.length);
    expect(next.cycleId).toBe(3);
    expect(next.iou).toBe(0.42);
  });
});
