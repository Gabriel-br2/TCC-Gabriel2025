#!/usr/bin/env python3
import asyncio
import datetime
import json
import logging
import random

import websockets

from objects import SHAPE_CLASSES
from screen_server import ScreenMonitor
from utils.collision import get_axis_aligned_bounding_box, aabbs_intersect
from utils.config import YamlConfig
from utils.logger import LoggerData
from utils.objective import apply_transformation, calculate_goal_area, calculate_progress, calculate_union_area, reorganize_data

# --- Config ---
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

cfg = YamlConfig("config")
cfg.read_config()

color = YamlConfig("color")
color.read_config()

player_colors = list(color.data.keys())[1:]

num_objects = cfg.data["game"]["objectsNum"]
num_players = cfg.data["game"]["playerNum"]
screen_width = cfg.data["screen"]["width"]
screen_height = cfg.data["screen"]["height"]
show_monitor = cfg.data["server"]["showMonitor"]

server_ip = "0.0.0.0"
server_port = cfg.data["server"]["port"]

# --- Object models ---
model_vertices = {key: cls(cfg).vertices for key, cls in SHAPE_CLASSES.items()}
object_options = list(SHAPE_CLASSES.keys())


class GameServer:
    def __init__(self):
        self.cycle_id = 0
        self.clients: dict = {}
        self.next_player_id = 0
        self.lock = asyncio.Lock()
        self.monitor = None

        self.timestamp = datetime.datetime.now().strftime("%d_%m_%H_%M_%S")
        self.logger = LoggerData(self.timestamp, player_colors)
        self.logger.log_metadata(cfg.data)

        self.objects, self.goal_area = self.generate_cycle()

    def place_object(self, obj_type, existing_positions, max_attempts=100):
        vertices = model_vertices[obj_type]

        for _ in range(max_attempts):
            x, y = random.randint(0, screen_width), random.randint(0, screen_height)
            rotation = random.choice([0, 90, 180, 270])

            transformed = apply_transformation(x, y, rotation, vertices)
            aabb = get_axis_aligned_bounding_box(transformed)
            min_x, min_y, max_x, max_y = aabb

            if min_x < 0 or min_y < 0 or max_x > screen_width or max_y > screen_height:
                continue

            if not any(
                aabbs_intersect(aabb, other_aabb)
                for *_, other_aabb in existing_positions
            ):
                return [x, y, rotation, obj_type, aabb]

        return None

    def generate_cycle(self):
        self.cycle_id += 1
        logging.info(f"Generating a new cycle... (ID: {self.cycle_id})")

        chosen_objects = random.choices(object_options, k=num_objects)
        new_objects = {}
        for pid in range(num_players):
            positions = []
            for obj in chosen_objects:
                placed = self.place_object(obj, positions)
                if placed:
                    positions.append(placed)
            new_objects[f"P{pid}"] = {
                "id": pid,
                "color": player_colors[pid],
                "pos": [p[:4] for p in positions],
            }
        new_objects["IoU"] = 0
        new_objects["cycle_id"] = self.cycle_id
        new_goal_area = calculate_goal_area([model_vertices[o] for o in chosen_objects])

        return new_objects, new_goal_area

    async def handler(self, websocket):
        async with self.lock:
            if self.next_player_id >= num_players:
                await websocket.close()
                return
            player_id = self.next_player_id
            self.next_player_id += 1
            self.clients[websocket] = player_id

        logging.info(f"Connection established with {websocket.remote_address}")

        try:
            await self._serve_client(websocket, player_id)
        except websockets.ConnectionClosed:
            pass
        except Exception as e:  # noqa: BLE001 - keep server alive on client errors
            logging.error(f"Client {player_id} error: {e}")
        finally:
            logging.info(f"Client {player_id} disconnected.")
            async with self.lock:
                self.clients.pop(websocket, None)

    async def _serve_client(self, websocket, player_id):
        raw = await websocket.recv()
        init_client_data = json.loads(raw)

        nature = init_client_data.get("nature")
        name_id = init_client_data.get("name")
        if nature == "LLM":
            name_id = f"{name_id}_LLM"

        logging.info(f"Client {player_id} identified as {nature} is {name_id}.")
        self.logger.log_player(player_id, name_id)

        async with self.lock:
            initial_data = {
                "objects": self.objects,
                "id": player_id,
                "timestamp": self.timestamp,
                "reset": False,
            }
        await websocket.send(json.dumps(initial_data))

        player_key = f"P{player_id}"
        async for message in websocket:
            try:
                update = json.loads(message)
            except json.JSONDecodeError:
                continue

            update_cycle_id = update.get("cycle_id")
            async with self.lock:
                if update_cycle_id == self.cycle_id and player_key in self.objects:
                    self.objects[player_key]["pos"] = update["pos"]

    async def calc_loop(self):
        self.monitor = (
            ScreenMonitor(cfg.data, color.data, model_vertices)
            if show_monitor
            else None
        )

        while True:
            objective = False
            if len(self.clients) == num_players:
                async with self.lock:
                    reset_cycle = False
                    reorganized = reorganize_data(self.objects, model_vertices)
                    union_area = calculate_union_area(reorganized)
                    progress = calculate_progress(
                        num_players, self.goal_area, union_area
                    )
                    self.objects["IoU"] = progress

                    if progress >= 0.95:
                        objective = True
                        logging.info(
                            f"Objective reached with {progress:.2f}%! Resetting cycle."
                        )
                        self.objects, self.goal_area = self.generate_cycle()
                        reset_cycle = True

                    data_to_send = json.dumps(
                        {"objects": self.objects, "reset": reset_cycle}
                    )
                    client_list_copy = list(self.clients.keys())
                    snapshot_goal_area = self.goal_area

                if client_list_copy:
                    websockets.broadcast(client_list_copy, data_to_send)
                    self.logger.log_event(
                        "objective_progress",
                        {
                            "goal_area": snapshot_goal_area,
                            "cycle_id": self.cycle_id,
                            "union_area": union_area,
                            "progress": progress,
                        },
                    )
                    if objective:
                        self.logger.log_event(
                            "Objective reached", {"cycle_id": self.cycle_id}
                        )

                    if self.monitor:
                        self.monitor.game_loop(self.objects, progress)

            await asyncio.sleep(0.25)

    async def run(self):
        async with websockets.serve(self.handler, server_ip, server_port):
            logging.info("Server started. Waiting for connections...")
            await self.calc_loop()


# --- main Loop ---
if __name__ == "__main__":
    server = GameServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logging.info("Server shutting down.")
        server.logger.process_data()
