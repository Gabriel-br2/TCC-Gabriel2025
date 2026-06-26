#!/usr/bin/env python3
import argparse
import time

from objects import SHAPE_CLASSES
from screen import Screen
from utils.config import YamlConfig
from utils.network import GameClient

# --- Variáveis Globais ---
game_is_running = True
current_cycle_id = 0

# --- Configuração de Argumentos ---
parser = argparse.ArgumentParser()
parser.add_argument(
    "--player",
    type=str,
    choices=["human", "LLM"],
    required=True,
    help="Choose the type of player",
)
parser.add_argument(
    "--source",
    type=str,
    choices=["api", "local"],
    help="LLM source (required if --player=LLM)",
)
parser.add_argument(
    "--name",
    type=str,
    help="Specify name of the agent (required if --player=LLM)",
)
parser.add_argument(
    "--memory",
    type=str,
    help="path for memory history for LLM agent (optional, default is None)",
)

args = parser.parse_args()
if args.player == "LLM":
    if not args.source:
        parser.error("The --source argument is required when --player is LLM.")
    if not args.name:
        parser.error("The --name argument is required when --player is LLM.")

if args.player == "human":
    if args.source:
        parser.error("The --source argument is not valid when --player is human.")
    if args.memory:
        parser.error("The --memory argument is not valid when --player is human.")


# --- Leitura de Configurações ---
cfg = YamlConfig("config")
color = YamlConfig("color")
cfg.read_config()
color.read_config()

screen = Screen(cfg.data, color.data, args.player, args.name, args.memory)

client = GameClient(cfg, args.player, screen.name_id)
initial_data = None
attempt_count = 0
while screen.game_running and initial_data is None:
    if not screen.show_waiting_screen(attempt_count):
        game_is_running = False
        break

    initial_data = client.connect()

    if initial_data is None:
        time.sleep(2)

    attempt_count += 1

if initial_data:
    client_id = client.client_id
    timestamp = client.timestamp

    screen.setup_player_specifics(client_id, timestamp, args.source)

    received_objects = initial_data["objects"]
    current_cycle_id = received_objects.get("cycle_id", 0)

    def initialize_objects(objects_data):
        shapes = []
        non_player_keys = ["IoU", "cycle_id"]
        for player, value in objects_data.items():
            if player in non_player_keys:
                continue

            transparency = (
                255 if player == f"P{client_id}" else cfg.data["game"]["transparency"]
            )
            player_color = [*color.data[value["color"]], transparency]

            for count, obj in enumerate(value["pos"]):
                shapes.append(
                    SHAPE_CLASSES[obj[-1]](
                        cfg,
                        int(player[1:]),
                        count,
                        screen.screen,
                        player_color,
                        obj[:-1],
                    )
                )
        return sorted(shapes, key=lambda s: (s.id != client_id, s.id, s.obj_id))

    shapes = initialize_objects(received_objects)
    iou = received_objects.get("IoU", 0)

    def start_game():
        global iou, shapes, game_is_running, current_cycle_id

        c = 0
        while screen.game_running and game_is_running:
            c += 1
            update_payload = screen.game_loop(shapes, iou)

            if c == 1 or (c % 25) == 0:
                if update_payload:
                    client.send_position(update_payload, current_cycle_id)

            if client.error is not None:
                print(
                    f"Erro na conexão com o servidor: {client.error}. Encerrando o jogo."
                )
                game_is_running = False
                break

            current_update = client.get_state()

            if current_update:
                is_reset = current_update.get("reset", False)
                server_objects = current_update.get("objects", {})

                if "cycle_id" in server_objects:
                    current_cycle_id = server_objects["cycle_id"]

                if is_reset:
                    print(
                        f"🚀 Novo ciclo ({current_cycle_id}) iniciado! Reinicializando objetos."
                    )
                    shapes = initialize_objects(server_objects)
                    screen.change_screen()
                else:
                    for shape in shapes:
                        if shape.id != client_id:
                            player_key = f"P{shape.id}"
                            if player_key in server_objects:
                                try:
                                    new_pos = server_objects[player_key]["pos"][
                                        shape.obj_id
                                    ]
                                    shape.position = new_pos[:-1]
                                except (KeyError, IndexError):
                                    pass

                iou = server_objects.get("IoU", iou)

        game_is_running = False
        screen.end_screen()

    if __name__ == "__main__":
        start_game()

client.close()
screen.close()
print("Programa encerrado.")
