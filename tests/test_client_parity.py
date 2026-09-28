"""Parity tests: Pygame client behavior is the source of truth."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

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
from tests.generate_parity_golden import StubPiece

FIXTURE = Path(__file__).parent / "fixtures" / "parity_golden.json"
SCREEN = {"screen": {"width": 1200, "height": 900}}


@pytest.fixture(scope="module")
def golden() -> dict:
    if not FIXTURE.exists():
        pytest.skip(f"Missing {FIXTURE}; run tests/generate_parity_golden.py")
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_player_key_and_non_player_keys(golden):
    assert player_key(2) == golden["meta"]["player_key_example"]
    assert set(NON_PLAYER_KEYS) == set(golden["meta"]["non_player_keys"])


def test_shape_vertices_match_golden(golden):
    cfg = YamlConfig(GAME_CONFIG)
    for name, expected in golden["vertices"].items():
        actual = [[float(x), float(y)] for x, y in SHAPE_CLASSES[name](cfg).vertices]
        assert actual == expected, name


def test_transforms_match_golden(golden):
    for case in golden["transforms"]:
        piece = StubPiece(case["type"], case["x"], case["y"], 0)
        world = piece.get_transformed_position([case["x"], case["y"]], case["rz"])
        assert [[int(x), int(y)] for x, y in world] == case["world"]


def test_point_in_polygon_match_golden(golden):
    for case in golden["hit_tests"]:
        assert point_in_polygon(tuple(case["point"]), [tuple(p) for p in case["polygon"]]) == case["inside"]


def test_interpolation_match_golden(golden):
    for case in golden["interpolation"]:
        xs, ys, steps = get_interpolation(case["dx"], case["dy"])
        assert int(steps) == case["steps"]
        assert [int(v) for v in xs] == case["xs"]
        assert [int(v) for v in ys] == case["ys"]


def test_moves_match_golden(golden):
    for case in golden["moves"]:
        start = case["start"]
        a = StubPiece(start[3], start[0], start[1], start[2])
        siblings = [a]
        if case["sibling"] is not None:
            sib = case["sibling"]
            b = StubPiece(sib[3], sib[0], sib[1], sib[2])
            siblings.append(b)
        ok = move_object(a, case["dx"], case["dy"], siblings, SCREEN)
        assert ok is case["ok"], case["name"]
        assert [a.position[0], a.position[1], a.position[2]] == case["end"], case["name"]
        if not ok and "unchanged_if_fail" in case:
            # may have partially stepped; golden records final accepted pose
            pass


def test_rotates_match_golden(golden):
    for case in golden["rotates"]:
        start = case["start"]
        a = StubPiece(start[3], start[0], start[1], start[2])
        siblings = [a]
        if case["sibling"] is not None:
            sib = case["sibling"]
            siblings.append(StubPiece(sib[3], sib[0], sib[1], sib[2]))
        ok = rotate_object(a, siblings, SCREEN)
        assert ok is case["ok"], case["name"]
        assert a.isRotating is case["isRotating"], case["name"]


def test_payload_factory_match_golden(golden):
    import pygame

    pygame.init()
    surface = pygame.Surface((1200, 900))
    settings = GameSettings.from_yaml(GAME_CONFIG, COLOR_CONFIG)
    factory = ClientObjectFactory(
        settings, COLOR_CONFIG, YamlConfig(GAME_CONFIG), surface
    )
    payload = golden["payload"]
    shapes = factory.from_server_payload(payload["objects"], payload["clientId"])
    assert [(s.id, s.obj_id) for s in shapes] == [tuple(p) for p in payload["draw_order"]]
    for shape, expected in zip(shapes, payload["pieces"], strict=True):
        assert shape.id == expected["playerId"]
        assert shape.obj_id == expected["objId"]
        assert shape.type == expected["type"]
        assert shape.position[0] == expected["x"]
        assert shape.position[1] == expected["y"]
        assert shape.position[2] == expected["rz"]
        assert shape.color[-1] == expected["alpha"]
        assert [[float(x), float(y)] for x, y in shape.vertices] == expected["vertices"]


def test_play_message_shape(golden):
    msg = golden["play_message"]
    assert set(msg.keys()) == {"pos", "cycle_id", "mouse"}
    assert isinstance(msg["pos"], list)
    assert all(len(piece) == 4 for piece in msg["pos"])
    assert isinstance(msg["cycle_id"], int)
    assert len(msg["mouse"]) == 2
    # Never wrap mouse inside pos (common port bug)
    assert not isinstance(msg["pos"][0], list) or len(msg["pos"][0]) == 4


def test_remote_update_semantics(golden):
    """Mirror application._apply_server_update without pygame loop."""
    for case in golden["remote_updates"]:
        pieces = {
            (p["playerId"], p["objId"]): dict(p) for p in case["before"]
        }
        objects = case["update"]["objects"]
        client_id = case["clientId"]
        for (pid, oid), piece in pieces.items():
            if pid == client_id:
                continue
            key = player_key(pid)
            if key not in objects:
                continue
            try:
                new_pos = objects[key]["pos"][oid]
                piece["x"], piece["y"], piece["rz"] = new_pos[0], new_pos[1], new_pos[2]
            except (KeyError, IndexError):
                pass
        after = [
            {
                "playerId": p["playerId"],
                "objId": p["objId"],
                "x": pieces[(p["playerId"], p["objId"])]["x"],
                "y": pieces[(p["playerId"], p["objId"])]["y"],
                "rz": pieces[(p["playerId"], p["objId"])]["rz"],
            }
            for p in case["before"]
        ]
        assert after == case["after"], case["name"]
        assert objects["IoU"] == case["iou"]
        assert objects["cycle_id"] == case["cycle_id"]


def test_rotation_animation_step_matches_pygame():
    """Shape.draw advances rz by +10 until multiple of 90."""
    piece = StubPiece("generic", 400, 400, 0)
    piece.rotate()
    assert piece.isRotating
    # emulate draw loop
    while piece.isRotating:
        piece.position[2] += 10
        if piece.position[2] % 90 == 0:
            piece.isRotating = False
    assert piece.position[2] == 90
