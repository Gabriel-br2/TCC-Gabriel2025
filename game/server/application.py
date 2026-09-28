import asyncio
import datetime
import json
import logging
from collections.abc import Callable
from typing import Any

import websockets

from game.server.cycle import CycleGenerator
from game.server.logger import SessionLogger
from game.server.monitor import ServerMonitor
from game.shared.game_state import GameState
from game.shared.objective import calculate_progress
from game.shared.objective import calculate_union_area
from game.shared.objective import reorganize_data
from game.shared.protocol import CALC_INTERVAL_SEC
from game.shared.protocol import OBJECTIVE_THRESHOLD
from game.shared.protocol import player_key
from game.shared.settings import GameSettings


class GameServer:
    def __init__(
        self,
        settings: GameSettings,
        cycle_generator: CycleGenerator,
        session_logger: SessionLogger,
        model_vertices: dict[str, list],
        monitor_factory: Callable[[], ServerMonitor | None] | None = None,
    ):
        self._settings = settings
        self._cycle_generator = cycle_generator
        self._logger = session_logger
        self._model_vertices = model_vertices
        self._monitor_factory = monitor_factory

        self.cycle_id = 0
        self.clients: dict[Any, int] = {}
        self._pending_clients: dict[Any, int] = {}
        self.player_info: dict[int, dict[str, Any]] = {}
        self.lock = asyncio.Lock()
        self.monitor: ServerMonitor | None = None
        self.objects: dict = {}
        self.goal_area = 0.0
        self.first_cycle = True
        self._shutting_down = False
        self._reset_hold_ticks = 0

        self._start_new_cycle()

    def _start_new_cycle(self) -> None:
        self.cycle_id += 1
        self.objects, self.goal_area = self._cycle_generator.generate(self.cycle_id)

    def _allocate_player_id(self) -> int | None:
        occupied = set(self.clients.values()) | set(self._pending_clients.values())
        for player_id in range(self._settings.num_players):
            if player_id not in occupied:
                return player_id
        return None

    async def handler(self, websocket):
        async with self.lock:
            player_id = self._allocate_player_id()
            if player_id is None:
                await websocket.close()
                return
            self._pending_clients[websocket] = player_id

        logging.info(f"Connection established with {websocket.remote_address}")

        try:
            await self._serve_client(websocket, player_id)
        except websockets.ConnectionClosed:
            pass
        except Exception as error:  # noqa: BLE001 - keep server alive on client errors
            logging.error(f"Client {player_id} error: {error}")
        finally:
            logging.info(f"Client {player_id} disconnected.")
            async with self.lock:
                self._pending_clients.pop(websocket, None)
                self.clients.pop(websocket, None)

    async def _serve_client(self, websocket, player_id: int):
        raw = await websocket.recv()
        init_client_data = json.loads(raw)

        nature = init_client_data.get("nature")
        name_id = init_client_data.get("name")
        if nature == "LLM":
            name_id = f"{name_id}_LLM"

        logging.info(f"Client {player_id} identified as {nature} is {name_id}.")
        self._logger.log_player(player_id, name_id)

        async with self.lock:
            self._pending_clients.pop(websocket, None)
            self.clients[websocket] = player_id
            self.player_info[player_id] = {
                "nature": nature,
                "name": name_id,
            }
            initial_data = GameState(
                objects=self.objects,
                iou=self.objects.get("IoU", 0.0),
                cycle_id=self.cycle_id,
                is_paused=len(self.clients) < self._settings.num_players,
                connected_players=len(self.clients),
                total_players=self._settings.num_players,
                reset=False,
            ).to_broadcast()
            initial_data["id"] = player_id
            initial_data["timestamp"] = self._logger.timestamp
        await websocket.send(json.dumps(initial_data))

        player_key_name = player_key(player_id)
        async for message in websocket:
            try:
                update = json.loads(message)
            except json.JSONDecodeError:
                continue

            update_cycle_id = update.get("cycle_id")
            async with self.lock:
                if update_cycle_id == self.cycle_id and player_key_name in self.objects:
                    incoming_pos = update.get("pos", [])
                    current_pos = self.objects[player_key_name].get("pos", [])
                    # Authority for shape types stays with the server/cycle.
                    # Clients may only update pose (x, y, rz).
                    merged_pos = []
                    for index, piece in enumerate(incoming_pos):
                        if (
                            index < len(current_pos)
                            and isinstance(piece, (list, tuple))
                            and len(piece) >= 4
                        ):
                            merged_pos.append(
                                [piece[0], piece[1], piece[2], current_pos[index][3]]
                            )
                        else:
                            merged_pos.append(piece)
                    self.objects[player_key_name]["pos"] = merged_pos
                    self.objects[player_key_name]["mouse"] = update.get("mouse", (0, 0))

    async def calc_loop(self):
        if self._monitor_factory is not None:
            self.monitor = self._monitor_factory()

        while True:
            if self._shutting_down:
                break
            objective = False
            async with self.lock:
                connected_players = len(self.clients)
                is_paused = connected_players < self._settings.num_players
                reset_cycle = False
                progress = self.objects.get("IoU", 0.0)

                if not is_paused:
                    reorganized = reorganize_data(self.objects, self._model_vertices)
                    union_area = calculate_union_area(reorganized)
                    progress = calculate_progress(
                        self._settings.num_players, self.goal_area, union_area
                    )
                    self.objects["IoU"] = progress

                    if progress >= OBJECTIVE_THRESHOLD:
                        objective = True
                        logging.info(
                            f"Objective reached with {progress:.2f}%! Resetting cycle."
                        )
                        self._start_new_cycle()
                        reset_cycle = True
                        # Hold reset:true across several ticks so late/background
                        # clients still observe the rebuild signal.
                        self._reset_hold_ticks = 60
                    elif self._reset_hold_ticks > 0:
                        reset_cycle = True
                        self._reset_hold_ticks -= 1

                game_state = GameState(
                    objects=self.objects,
                    iou=progress,
                    cycle_id=self.cycle_id,
                    is_paused=is_paused,
                    connected_players=connected_players,
                    total_players=self._settings.num_players,
                    reset=reset_cycle,
                )
                data_to_send = json.dumps(game_state.to_broadcast())
                client_list_copy = list(self.clients.keys())
                snapshot_goal_area = self.goal_area

            if client_list_copy:
                websockets.broadcast(client_list_copy, data_to_send)

                if not is_paused:
                    self._logger.log_event(
                        "objective_progress",
                        {
                            "goal_area": snapshot_goal_area,
                            "cycle_id": self.cycle_id,
                            "union_area": union_area,
                            "progress": progress,
                        },
                    )
                    if objective:
                        self._logger.log_event(
                            "Objective reached", {"cycle_id": self.cycle_id}
                        )

                if self.monitor is not None:
                    if not self.monitor.observe(self.objects, progress):
                        break
                                
            await asyncio.sleep(0.25 if self.first_cycle else CALC_INTERVAL_SEC)  
            self.first_cycle = False 

    def snapshot(self, *, reveal_names: bool = False) -> dict[str, Any]:
        """Operator-facing session snapshot. Safe to call only while holding `lock`."""
        occupied = set(self.clients.values())
        slots = []
        for player_id in range(self._settings.num_players):
            info = self.player_info.get(player_id, {})
            raw_name = info.get("name")
            color = (
                self._settings.player_colors[player_id]
                if player_id < len(self._settings.player_colors)
                else None
            )
            slots.append(
                {
                    "id": player_id,
                    "color": color,
                    "connected": player_id in occupied,
                    "nature": info.get("nature"),
                    "name_masked": _mask_name(raw_name),
                    "name": raw_name if reveal_names else None,
                }
            )

        objects_view = _snapshot_objects_for_admin(self.objects)
        return {
            "cycle_id": self.cycle_id,
            "iou": float(self.objects.get("IoU", 0.0) or 0.0),
            "is_paused": len(self.clients) < self._settings.num_players,
            "connected_players": len(self.clients),
            "total_players": self._settings.num_players,
            "goal_area": self.goal_area,
            "slots": slots,
            "objects": objects_view,
        }

    async def get_snapshot(self, *, reveal_names: bool = False) -> dict[str, Any]:
        async with self.lock:
            return self.snapshot(reveal_names=reveal_names)

    def public_client_config(self, request_host: str) -> dict[str, Any]:
        from game.shared.config import COLOR_CONFIG

        hostname = request_host.split(":")[0]
        connect_host = self._settings.server_connect_host
        if "ngrok" in hostname.lower() or (
            "ngrok" in connect_host.lower() and hostname not in {"localhost", "127.0.0.1", "::1"}
            and not hostname.startswith("192.168.")
            and not hostname.startswith("10.")
        ):
            ws_url = f"wss://{connect_host}"
        else:
            ws_url = f"ws://{hostname}:{self._settings.server_port}"
        return {
            "screen": {
                "caption": self._settings.screen_caption,
                "width": self._settings.screen_width,
                "height": self._settings.screen_height,
            },
            "game": {
                "playerNum": self._settings.num_players,
                "objectsNum": self._settings.num_objects,
                "objectBaseSquareTam": self._settings.object_base_square_size,
                "transparency": self._settings.transparency,
            },
            "ws": {"url": ws_url, "port": self._settings.server_port},
            "player_colors": list(self._settings.player_colors),
            "colors": COLOR_CONFIG,
        }

    def operator_config(self) -> dict[str, Any]:
        from game.shared.config import COLOR_CONFIG
        from game.shared.config import GAME_CONFIG

        return {
            "settings": {
                "screen_width": self._settings.screen_width,
                "screen_height": self._settings.screen_height,
                "screen_caption": self._settings.screen_caption,
                "num_players": self._settings.num_players,
                "num_objects": self._settings.num_objects,
                "object_base_square_size": self._settings.object_base_square_size,
                "transparency": self._settings.transparency,
                "server_bind_host": self._settings.server_bind_host,
                "server_connect_host": self._settings.server_connect_host,
                "server_port": self._settings.server_port,
                "show_monitor": self._settings.show_monitor,
                "player_colors": list(self._settings.player_colors),
            },
            "game_config": GAME_CONFIG,
            "color_config": COLOR_CONFIG,
            "log_timestamp": self._logger.timestamp,
        }

    async def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True

        if self.monitor is not None:
            self.monitor.close()

        async with self.lock:
            client_list_copy = list(self.clients.keys())

        if client_list_copy:
            shutdown_msg = json.dumps({"type": "shutdown"})
            websockets.broadcast(client_list_copy, shutdown_msg)
            await asyncio.sleep(0.1)
            await asyncio.gather(
                *[ws.close() for ws in client_list_copy],
                return_exceptions=True,
            )
            logging.info(f"Shutdown sent to {len(client_list_copy)} client(s).")

        try:
            self._logger.process_data()
        except Exception:
            logging.exception("Failed to process session plots during shutdown")

    async def run(self):
        from game.server.admin import start_admin_site

        admin_runner = None
        try:
            admin_runner = await start_admin_site(self)
            async with websockets.serve(
                self.handler,
                self._settings.server_bind_host,
                self._settings.server_port,
            ):
                logging.info("Server started. Waiting for connections...")
                await self.calc_loop()
        except OSError as error:
            if error.errno == 98:
                logging.error(
                    f"Port {self._settings.server_port} is already in use. "
                    f"use lsof -i :{self._settings.server_port} to find the process using it"
                    "kill the process with kill -9 <PID> and try again."
                )
            else:
                logging.error(f"Server encountered an OSError: {error}")
        finally:
            await self.shutdown()
            if admin_runner is not None:
                await admin_runner.cleanup()


def _mask_name(name: str | None) -> str | None:
    if not name:
        return None
    parts = [part for part in str(name).split() if part]
    if not parts:
        return None
    return " ".join(f"{part[0]}." for part in parts)


def _snapshot_objects_for_admin(objects: dict) -> dict:
    snapshot: dict[str, Any] = {}
    for key, value in objects.items():
        if key in ("IoU", "cycle_id"):
            snapshot[key] = value
            continue
        if not isinstance(value, dict):
            continue
        mouse = value.get("mouse")
        snapshot[key] = {
            "id": value.get("id"),
            "color": value.get("color"),
            "pos": [list(obj) for obj in value.get("pos", [])],
            "mouse": list(mouse) if mouse is not None else None,
        }
    return snapshot