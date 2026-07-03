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
        self.lock = asyncio.Lock()
        self.monitor: ServerMonitor | None = None
        self.objects: dict = {}
        self.goal_area = 0.0

        self._start_new_cycle()

    def _start_new_cycle(self) -> None:
        self.cycle_id += 1
        self.objects, self.goal_area = self._cycle_generator.generate(self.cycle_id)

    def _allocate_player_id(self) -> int | None:
        occupied = set(self.clients.values())
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
            self.clients[websocket] = player_id

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
                    if not self.monitor.render_frame(self.objects, progress):
                        break

            await asyncio.sleep(CALC_INTERVAL_SEC)

    async def shutdown(self) -> None:
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