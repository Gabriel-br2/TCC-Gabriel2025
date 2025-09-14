#!/usr/bin/env python3
import argparse
import threading
import time

from objects.generic import GenericShape
from objects.teewee import TeeweeShape
from screen import Screen
from utils.config import YamlConfig
from utils.network import establish_client_connection
from utils.network import receive_new_position
from utils.network import send_new_position


latest_server_state = {}
state_lock = threading.Lock()
game_is_running = True

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
args = parser.parse_args()
if args.player == "LLM" and not args.source:
    parser.error("The --source argument is required when --player is LLM.")
if args.player == "human" and args.source:
    parser.error("The --source argument is not valid when --player is human.")

cfg = YamlConfig("config")
color = YamlConfig("color")
cfg.read_config()
color.read_config()

client_socket, client_id, initial_data = establish_client_connection(cfg)
received_objects = initial_data["objects"]

shape_classes = {"generic": GenericShape, "teewee": TeeweeShape}
screen = Screen(cfg.data, color.data, client_id, args.player)


def initialize_objects(objects_data):
    shapes = []
    for player, value in objects_data.items():
        if player == "IoU":
            continue
        transparency = (
            255 if player == f"P{client_id}" else cfg.data["game"]["transparency"]
        )
        player_color = [*color.data[value["color"]], transparency]
        for count, obj in enumerate(value["pos"]):
            shapes.append(
                shape_classes[obj[-1]](
                    cfg, int(player[1:]), count, screen.screen, player_color, obj[:-1]
                )
            )
    return sorted(shapes, key=lambda s: (s.id != client_id, s.id, s.obj_id))


def network_listener(sock):
    global latest_server_state, game_is_running
    while game_is_running:
        server_update = receive_new_position(sock)
        if server_update is None:
            print("Conexão com o servidor perdida. Encerrando o jogo.")
            game_is_running = False
            break

        with state_lock:
            latest_server_state = server_update


shapes = initialize_objects(received_objects)
iou = received_objects.get("IoU", 0)


def start_game():
    global iou, shapes, latest_server_state, game_is_running

    listener_thread = threading.Thread(
        target=network_listener, args=(client_socket,), daemon=True
    )
    listener_thread.start()

    while screen.game_running and game_is_running:
        update_payload = screen.game_loop(shapes, iou)

        send_new_position(client_socket, update_payload)

        current_update = None
        with state_lock:
            if latest_server_state:  # Verifica se a thread de rede recebeu algo novo
                current_update = latest_server_state
                latest_server_state = (
                    {}
                )  # Limpa para não processar a mesma mensagem duas vezes

        if current_update:
            is_reset = current_update.get("reset", False)
            server_objects = current_update.get("objects", {})

            if is_reset:
                print("🚀 New cycle started! Re-initializing objects.")
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
    screen.close()


if __name__ == "__main__":
    start_game()
