"""Client-side networking built on websockets and asyncio."""

import asyncio
import json
import threading
from typing import Optional

import websockets

from game.shared.settings import GameSettings

CONNECT_TIMEOUT = 2.0
HANDSHAKE_TIMEOUT = 10.0
SEND_TIMEOUT = 5.0


class GameClient:
    def __init__(self, settings: GameSettings, nature: str, name: str | None = None):
        self.server_ip = settings.server_connect_host
        self.port = settings.server_port
        self.nature = nature
        self.name = name

        self.client_id = None
        self.timestamp = None
        self.initial_data = None
        self.error = None

        self._websocket = None
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        self._state_lock = threading.Lock()
        self._latest_state: dict = {}

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _submit(self, coro, timeout=None):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    def connect(self) -> Optional[dict]:
        try:
            return self._submit(
                self._connect(), timeout=CONNECT_TIMEOUT + HANDSHAKE_TIMEOUT
            )
        except (OSError, asyncio.TimeoutError, websockets.WebSocketException) as error:
            print(f"Falha ao conectar ao servidor: {error}. Tentando novamente...")
            return None

    async def _connect(self) -> dict:
        uri = f"ws://{self.server_ip}:{self.port}"
        print(f"Tentando conectar a {uri}...")
        self._websocket = await websockets.connect(uri, open_timeout=CONNECT_TIMEOUT)
        print("Cliente conectado ao servidor!")

        identification = {"nature": self.nature, "name": self.name}
        await self._websocket.send(json.dumps(identification))

        raw = await asyncio.wait_for(self._websocket.recv(), timeout=HANDSHAKE_TIMEOUT)
        print("Cliente - Dados iniciais recebidos")
        data = json.loads(raw)

        self.client_id = data["id"]
        self.timestamp = data["timestamp"]
        self.initial_data = data

        self._loop.create_task(self._receive_loop())
        return data

    async def _receive_loop(self):
        try:
            async for message in self._websocket:
                try:
                    update = json.loads(message)
                except json.JSONDecodeError:
                    print("Erro ao decodificar os dados recebidos do servidor.")
                    continue

                with self._state_lock:
                    self._latest_state = update
        except websockets.ConnectionClosed:
            print("Servidor fechou a conexão.")
            self.error = "disconnected"
        except Exception as error:  # noqa: BLE001
            print(f"Erro ao receber dados: {error}")
            self.error = str(error)

    def get_state(self) -> Optional[dict]:
        with self._state_lock:
            if self._latest_state:
                state = self._latest_state
                self._latest_state = {}
                return state
        return None

    def send_position(self, new_position, current_cycle_id, mouse_position):
        message = {"pos": new_position, "cycle_id": current_cycle_id, "mouse": mouse_position}
        try:
            self._submit(
                self._websocket.send(json.dumps(message)), timeout=SEND_TIMEOUT
            )
        except websockets.ConnectionClosed as e:
            print(f"Erro ao enviar posição: {e}")
            self.error = e
        except Exception as error:  # noqa: BLE001
            print(f"Erro ao enviar posição: {error}")

    def close(self):
        if self._websocket is not None:
            try:
                self._submit(self._websocket.close(), timeout=SEND_TIMEOUT)
            except Exception:  # noqa: BLE001
                pass
        self._loop.call_soon_threadsafe(self._loop.stop)
