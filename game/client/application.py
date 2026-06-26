import time

from game.client.network import GameClient
from game.client.objects import ClientObjectFactory
from game.client.screen import Screen
from game.shared.game_state import GameState
from game.shared.protocol import SEND_EVERY_N_FRAMES
from game.shared.protocol import player_key
from game.shared.settings import GameSettings


class ClientApplication:
    def __init__(
        self,
        screen: Screen,
        network: GameClient,
        object_factory: ClientObjectFactory,
        settings: GameSettings,
    ):
        self._screen = screen
        self._network = network
        self._object_factory = object_factory
        self._settings = settings

        self._running = True
        self._client_id: int | None = None
        self._game_state: GameState | None = None

    def connect_until_ready(self) -> dict | None:
        attempt_count = 0
        while self._screen.game_running:
            if not self._screen.show_waiting_screen(attempt_count):
                self._running = False
                return None

            initial_data = self._network.connect()
            if initial_data is not None:
                return initial_data

            time.sleep(2)
            attempt_count += 1
        return None

    def start_session(self, initial_data: dict, llm_source: str | None) -> None:
        self._client_id = self._network.client_id
        self._screen.setup_player_specifics(
            self._client_id, self._network.timestamp, llm_source
        )

        shapes = self._object_factory.from_server_payload(
            initial_data["objects"], self._client_id
        )
        self._game_state = GameState.from_broadcast(initial_data, shapes)
        self._run_loop()

    def _run_loop(self) -> None:
        tick = 24
        while self._screen.game_running and self._running:
            tick += 1
            update_payload = self._screen.game_loop(self._game_state)

            if (
                not self._game_state.is_paused
                and tick % SEND_EVERY_N_FRAMES == 0
                and update_payload
            ):
                self._network.send_position(update_payload, self._game_state.cycle_id)

            if self._network.error is not None:
                print(
                    f"Erro na conexão com o servidor: {self._network.error}. "
                    "Encerrando o jogo."
                )
                self._running = False
                break

            current_update = self._network.get_state()
            if current_update:
                self._game_state = self._apply_server_update(current_update)

        self._screen.end_screen()

    def _apply_server_update(self, update: dict) -> GameState:
        server_objects = update.get("objects", {})
        is_reset = update.get("reset", False)

        if is_reset:
            print(
                f"🚀 Novo ciclo ({server_objects.get('cycle_id', 0)}) iniciado! "
                "Reinicializando objetos."
            )
            shapes = self._object_factory.from_server_payload(
                server_objects, self._client_id
            )
            self._screen.change_screen()
        else:
            shapes = self._game_state.objects
            for shape in shapes:
                if shape.id != self._client_id:
                    key = player_key(shape.id)
                    if key in server_objects:
                        try:
                            new_pos = server_objects[key]["pos"][shape.obj_id]
                            shape.position = new_pos[:-1]
                        except (KeyError, IndexError):
                            pass

        return GameState.from_broadcast(update, shapes)

    def shutdown(self) -> None:
        self._network.close()
        self._screen.close()
