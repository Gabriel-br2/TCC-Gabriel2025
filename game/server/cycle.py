import logging
import random
from typing import Any

from game.shared.collision import aabbs_intersect
from game.shared.collision import get_axis_aligned_bounding_box
from game.shared.objective import apply_transformation
from game.shared.objective import calculate_goal_area
from game.shared.protocol import player_key
from game.shared.settings import GameSettings


class CycleGenerator:
    def __init__(
        self,
        settings: GameSettings,
        model_vertices: dict[str, list],
        shape_options: list[str],
        rng: random.Random | None = None,
    ):
        self._settings = settings
        self._model_vertices = model_vertices
        self._shape_options = shape_options
        self._rng = rng or random.Random()

    def place_object(
        self, obj_type: str, existing_positions: list, max_attempts: int = 100
    ) -> list[Any] | None:
        vertices = self._model_vertices[obj_type]

        for _ in range(max_attempts):
            x = self._rng.randint(0, self._settings.screen_width)
            y = self._rng.randint(0, self._settings.screen_height)
            rotation = self._rng.choice([0, 90, 180, 270])

            transformed = apply_transformation(x, y, rotation, vertices)
            aabb = get_axis_aligned_bounding_box(transformed)
            min_x, min_y, max_x, max_y = aabb

            if (
                min_x < 0
                or min_y < 0
                or max_x > self._settings.screen_width
                or max_y > self._settings.screen_height
            ):
                continue

            if not any(
                aabbs_intersect(aabb, other_aabb)
                for *_, other_aabb in existing_positions
            ):
                return [x, y, rotation, obj_type, aabb]

        return None

    def generate(self, cycle_id: int) -> tuple[dict, float]:
        logging.info(f"Generating a new cycle... (ID: {cycle_id})")

        chosen_objects = self._rng.choices(
            self._shape_options, k=self._settings.num_objects
        )
        new_objects: dict[str, Any] = {}
        for pid in range(self._settings.num_players):
            positions = []
            for obj in chosen_objects:
                placed = self.place_object(obj, positions)
                if placed:
                    positions.append(placed)
            new_objects[player_key(pid)] = {
                "id": pid,
                "color": self._settings.player_colors[pid],
                "pos": [p[:4] for p in positions],
            }
        new_objects["IoU"] = 0
        new_objects["cycle_id"] = cycle_id
        goal_area = calculate_goal_area(
            [self._model_vertices[o] for o in chosen_objects]
        )
        return new_objects, goal_area
