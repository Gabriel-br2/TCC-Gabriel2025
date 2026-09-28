"""Generate golden fixtures from the Pygame client (source of truth).

Run from repo root:
  ./venv/bin/python tests/generate_parity_golden.py
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from game.client.objects import ClientObjectFactory
from game.client.players.motion import get_interpolation
from game.client.players.motion import move_object
from game.client.players.motion import rotate_object
from game.shared.collision import point_in_polygon
from game.shared.config import COLOR_CONFIG
from game.shared.config import GAME_CONFIG
from game.shared.config import YamlConfig
from game.shared.protocol import NON_PLAYER_KEYS
from game.shared.protocol import player_key
from game.shared.settings import GameSettings
from game.shared.shapes import SHAPE_CLASSES


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "fixtures" / "parity_golden.json"
BASE = GAME_CONFIG["game"]["objectBaseSquareTam"]
SCREEN = {"screen": {"width": 1200, "height": 900}}


class StubPiece:
    """Minimal piece matching Shape motion API without rendering."""

    def __init__(self, shape_type: str, x: float, y: float, rz: float):
        cfg = YamlConfig(GAME_CONFIG)
        model = SHAPE_CLASSES[shape_type](cfg)
        self.vertices = list(model.vertices)
        self.type = shape_type
        self.position = [x, y, rz]
        self.isRotating = False

    def get_transformation_matrix(self, position, angle_deg):
        angle_rad = math.radians(angle_deg)
        c_theta = math.cos(angle_rad)
        s_theta = math.sin(angle_rad)
        tx, ty = position
        return [[c_theta, -s_theta, tx], [s_theta, c_theta, ty], [0, 0, 1]]

    def apply_transformation(self, vertex, matrix):
        x, y = vertex
        x_new = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]
        y_new = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]
        return (int(x_new), int(y_new))

    def get_transformed_position(self, position, angle):
        matrix = self.get_transformation_matrix(position, angle)
        return [self.apply_transformation(vertex, matrix) for vertex in self.vertices]

    def rotate(self):
        self.isRotating = True


def vertices_map() -> dict:
    cfg = YamlConfig(GAME_CONFIG)
    return {
        name: [[float(x), float(y)] for x, y in cls(cfg).vertices]
        for name, cls in SHAPE_CLASSES.items()
    }


def transform_cases() -> list:
    cases = []
    for shape_type in SHAPE_CLASSES:
        piece = StubPiece(shape_type, 400, 300, 0)
        for angle in (0, 90, 180, 270, 45):
            world = piece.get_transformed_position([400, 300], angle)
            cases.append(
                {
                    "type": shape_type,
                    "x": 400,
                    "y": 300,
                    "rz": angle,
                    "world": [[int(x), int(y)] for x, y in world],
                }
            )
    return cases


def hit_cases() -> list:
    piece = StubPiece("generic", 200, 200, 0)
    poly = piece.get_transformed_position([200, 200], 0)
    return [
        {"point": [200, 200], "polygon": [[int(x), int(y)] for x, y in poly], "inside": True},
        {"point": [10, 10], "polygon": [[int(x), int(y)] for x, y in poly], "inside": False},
        {"point": [200, 200], "polygon": [[100, 100], [300, 100], [300, 300], [100, 300]], "inside": True},
        {"point": [50, 50], "polygon": [[100, 100], [300, 100], [300, 300], [100, 300]], "inside": False},
    ]


def interpolation_cases() -> list:
    samples = [(0, 0), (5, 0), (0, -3), (10, 4), (-7, 2)]
    out = []
    for dx, dy in samples:
        xs, ys, steps = get_interpolation(dx, dy)
        out.append(
            {
                "dx": dx,
                "dy": dy,
                "steps": int(steps),
                "xs": [int(v) for v in xs],
                "ys": [int(v) for v in ys],
            }
        )
    return out


def move_cases() -> list:
    cases = []

    # free move
    a = StubPiece("generic", 400, 400, 0)
    b = StubPiece("generic", 700, 700, 0)
    ok = move_object(a, 20, -10, [a, b], SCREEN)
    cases.append(
        {
            "name": "free_move",
            "start": [400, 400, 0, "generic"],
            "sibling": [700, 700, 0, "generic"],
            "dx": 20,
            "dy": -10,
            "ok": ok,
            "end": [a.position[0], a.position[1], a.position[2]],
        }
    )

    # boundary reject (near left edge)
    a = StubPiece("generic", 30, 400, 0)
    b = StubPiece("generic", 700, 700, 0)
    before = [a.position[0], a.position[1], a.position[2]]
    ok = move_object(a, -100, 0, [a, b], SCREEN)
    cases.append(
        {
            "name": "boundary_reject",
            "start": [30, 400, 0, "generic"],
            "sibling": [700, 700, 0, "generic"],
            "dx": -100,
            "dy": 0,
            "ok": ok,
            "end": [a.position[0], a.position[1], a.position[2]],
            "unchanged_if_fail": before,
        }
    )

    # sibling collision reject
    a = StubPiece("generic", 400, 400, 0)
    b = StubPiece("generic", 460, 400, 0)
    before = [a.position[0], a.position[1], a.position[2]]
    ok = move_object(a, 40, 0, [a, b], SCREEN)
    cases.append(
        {
            "name": "sibling_collision_reject",
            "start": [400, 400, 0, "generic"],
            "sibling": [460, 400, 0, "generic"],
            "dx": 40,
            "dy": 0,
            "ok": ok,
            "end": [a.position[0], a.position[1], a.position[2]],
            "unchanged_if_fail": before,
        }
    )

    # zero delta
    a = StubPiece("hero", 500, 500, 90)
    ok = move_object(a, 0, 0, [a], SCREEN)
    cases.append(
        {
            "name": "zero_delta",
            "start": [500, 500, 90, "hero"],
            "sibling": None,
            "dx": 0,
            "dy": 0,
            "ok": ok,
            "end": [a.position[0], a.position[1], a.position[2]],
        }
    )

    return cases


def rotate_cases() -> list:
    cases = []

    a = StubPiece("hero", 400, 400, 0)
    b = StubPiece("generic", 800, 800, 0)
    ok = rotate_object(a, [a, b], SCREEN)
    cases.append(
        {
            "name": "rotate_ok",
            "start": [400, 400, 0, "hero"],
            "sibling": [800, 800, 0, "generic"],
            "ok": ok,
            "isRotating": a.isRotating,
        }
    )

    # near top: +90 may leave screen for tall/wide shapes
    a = StubPiece("hero", 100, 40, 0)
    before_rotating = a.isRotating
    ok = rotate_object(a, [a], SCREEN)
    cases.append(
        {
            "name": "rotate_boundary_reject",
            "start": [100, 40, 0, "hero"],
            "sibling": None,
            "ok": ok,
            "isRotating": a.isRotating,
            "was_rotating": before_rotating,
        }
    )

    a = StubPiece("generic", 400, 400, 0)
    b = StubPiece("generic", 430, 400, 0)
    ok = rotate_object(a, [a, b], SCREEN)
    cases.append(
        {
            "name": "rotate_sibling_reject",
            "start": [400, 400, 0, "generic"],
            "sibling": [430, 400, 0, "generic"],
            "ok": ok,
            "isRotating": a.isRotating,
        }
    )

    return cases


def payload_case() -> dict:
    pygame.init()
    surface = pygame.Surface((1200, 900))
    settings = GameSettings.from_yaml(GAME_CONFIG, COLOR_CONFIG)
    factory = ClientObjectFactory(
        settings, COLOR_CONFIG, YamlConfig(GAME_CONFIG), surface
    )
    objects = {
        "P0": {
            "id": 0,
            "color": "blue",
            "pos": [[200, 200, 0, "hero"], [350, 250, 90, "z"]],
        },
        "P1": {
            "id": 1,
            "color": "pink",
            "pos": [[600, 400, 180, "ricky"]],
        },
        "P2": {"id": 2, "color": "yellow", "pos": []},
        "IoU": 0.42,
        "cycle_id": 3,
    }
    client_id = 0
    shapes = factory.from_server_payload(objects, client_id)
    pieces = []
    for shape in shapes:
        pieces.append(
            {
                "playerId": shape.id,
                "objId": shape.obj_id,
                "type": shape.type,
                "x": shape.position[0],
                "y": shape.position[1],
                "rz": shape.position[2],
                "alpha": shape.color[-1],
                "vertices": [[float(x), float(y)] for x, y in shape.vertices],
            }
        )
    return {
        "clientId": client_id,
        "objects": objects,
        "transparency": settings.transparency,
        "pieces": pieces,
        "draw_order": [(p["playerId"], p["objId"]) for p in pieces],
    }


def remote_update_cases() -> list:
    """Document how app client applies non-reset broadcasts to other players."""
    return [
        {
            "name": "update_other_player_pose",
            "clientId": 0,
            "before": [
                {"playerId": 0, "objId": 0, "x": 100, "y": 100, "rz": 0, "type": "generic"},
                {"playerId": 1, "objId": 0, "x": 200, "y": 200, "rz": 0, "type": "generic"},
            ],
            "update": {
                "objects": {
                    "P0": {"color": "blue", "pos": [[100, 100, 0, "generic"]]},
                    "P1": {"color": "pink", "pos": [[250, 260, 90, "generic"]]},
                    "IoU": 0.5,
                    "cycle_id": 2,
                },
                "reset": False,
                "is_paused": False,
                "connected_players": 4,
                "total_players": 4,
            },
            "after": [
                {"playerId": 0, "objId": 0, "x": 100, "y": 100, "rz": 0},
                {"playerId": 1, "objId": 0, "x": 250, "y": 260, "rz": 90},
            ],
            "iou": 0.5,
            "cycle_id": 2,
        },
        {
            "name": "ignore_local_pose_from_broadcast",
            "clientId": 0,
            "before": [
                {"playerId": 0, "objId": 0, "x": 111, "y": 222, "rz": 45, "type": "hero"},
                {"playerId": 1, "objId": 0, "x": 200, "y": 200, "rz": 0, "type": "z"},
            ],
            "update": {
                "objects": {
                    "P0": {"color": "blue", "pos": [[999, 999, 180, "hero"]]},
                    "P1": {"color": "pink", "pos": [[210, 220, 270, "z"]]},
                    "IoU": 0.1,
                    "cycle_id": 1,
                },
                "reset": False,
            },
            "after": [
                {"playerId": 0, "objId": 0, "x": 111, "y": 222, "rz": 45},
                {"playerId": 1, "objId": 0, "x": 210, "y": 220, "rz": 270},
            ],
            "iou": 0.1,
            "cycle_id": 1,
        },
    ]


def play_message_example() -> dict:
    return {
        "pos": [[120, 210, 90, "hero"], [400, 300, 90, "z"]],
        "cycle_id": 1,
        "mouse": [512, 388],
    }


def main() -> None:
    golden = {
        "meta": {
            "source": "Pygame client (game/client + game/shared)",
            "objectBaseSquareTam": BASE,
            "screen": SCREEN["screen"],
            "non_player_keys": sorted(NON_PLAYER_KEYS),
            "player_key_example": player_key(2),
        },
        "vertices": vertices_map(),
        "transforms": transform_cases(),
        "hit_tests": hit_cases(),
        "interpolation": interpolation_cases(),
        "moves": move_cases(),
        "rotates": rotate_cases(),
        "payload": payload_case(),
        "remote_updates": remote_update_cases(),
        "play_message": play_message_example(),
        "ui_copy": {
            "identify_title": "Identificação do Jogador",
            "waiting": "Rodada já completada aguarde sua vez",
            "pause": "Jogo pausado. Aguardando jogadores {n}/{total}.",
            "hud": "Objetivo Concluído: {iou * 100:.2f} %",
            "cycle": "Objetivo concluído, iniciando próximo ciclo",
            "cycle_ms": 3000,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(golden, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
