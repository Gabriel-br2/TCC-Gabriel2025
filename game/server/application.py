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
from game.shared.objective import reorganize_data_map
from game.shared.objective import player_individual_polygons
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
        self.lock = asyncio.Lock()
        self.monitor: ServerMonitor | None = None
        self.objects: dict = {}
        self.goal_area = 0.0
        self.first_cycle = True
        # per-player overlap (guilt) counters
        self._guilt_hits: dict[int, int] = {i: 0 for i in range(self._settings.num_players)}

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
                    self.objects[player_key_name]["pos"] = update["pos"]
                    self.objects[player_key_name]["mouse"] = update.get("mouse", (0, 0))
                    # detect overlaps caused by this placement
                    self._detect_and_record_overlaps(player_key_name, player_id)

    def _detect_and_record_overlaps(self, player_key_name: str, player_id: int) -> None:
        """Detect overlaps caused by the most recent placement from `player_key_name`,
        update internal counters/state and log an event if overlaps occurred.
        """
        try:
            player_polys = player_individual_polygons(
                self.objects, self._model_vertices, player_key_name
            )
            others_map = reorganize_data_map(self.objects, self._model_vertices)
            others_map.pop(player_key_name, None)
            overlap_count = 0
            overlapped_with = set()
            for poly in player_polys:
                for ok, other_poly in others_map.items():
                    try:
                        if poly.intersects(other_poly):
                            overlap_count += 1
                            overlapped_with.add(ok)
                    except Exception:
                        continue

            if overlap_count > 0:
                self._guilt_hits[player_id] = self._guilt_hits.get(player_id, 0) + overlap_count
                try:
                    self.objects[player_key_name]["overlaps"] = int(overlap_count)
                    self.objects[player_key_name]["overlapped_with"] = list(overlapped_with)
                except Exception:
                    pass
                try:
                    self._logger.log_event(
                        "overlap_event",
                        {
                            "player_id": player_id,
                            "cycle_id": self.cycle_id,
                            "overlap_count": overlap_count,
                            "overlapped_with": list(overlapped_with),
                        },
                    )
                except Exception:
                    pass
        except Exception:
            pass

    async def calc_loop(self):
        if self._monitor_factory is not None:
            self.monitor = self._monitor_factory()

        while True:
            objective = False
            async with self.lock:
                connected_players = len(self.clients)
                is_paused = connected_players < self._settings.num_players
                reset_cycle = False
                progress = self.objects.get("IoU", 0.0)

                if not is_paused:
                    player_polygons = reorganize_data_map(self.objects, self._model_vertices)
                    polygons = list(player_polygons.values())
                    union_area = calculate_union_area(polygons) if polygons else 0.0
                    progress = calculate_progress(
                        self._settings.num_players, self.goal_area, union_area
                    )

                    # per-player marginal contribution computation removed; overlap events are used instead
                    self.objects["IoU"] = progress

                    if progress >= OBJECTIVE_THRESHOLD:
                        objective = True
                        logging.info(
                            f"Objective reached with {progress:.2f}%! Resetting cycle."
                        )
                        self._start_new_cycle()
                        reset_cycle = True

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
                    # per-player contributions removed; overlap_event used for attribution
                    if objective:
                        self._logger.log_event(
                            "Objective reached", {"cycle_id": self.cycle_id}
                        )

                if self.monitor is not None:
                    if not self.monitor.observe(self.objects, progress):
                        break
                                
            await asyncio.sleep(0.25 if self.first_cycle else CALC_INTERVAL_SEC)  
            self.first_cycle = False 

    async def shutdown(self) -> None:
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
 
        self._logger.process_data()

    async def run(self):
        try:
            
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