#!/usr/bin/env python3
from objects.generic import GenericShape
from objects.teewee import TeeweeShape
from screen import Screen
from utils.config import YamlConfig
from utils.network import establish_client_connection
from utils.network import receive_new_position
from utils.network import send_new_position

# --- Configs ---
cfg = YamlConfig("config")
color = YamlConfig("color")
cfg.read_config()
color.read_config()

# --- server Con ---
client_socket, client_id, received_objects = establish_client_connection(cfg)

# --- Start form ---
shape_classes = {"generic": GenericShape, "teewee": TeeweeShape}
screen = Screen(cfg.data, color.data, client_id)


def initialize_objects(received_objects):
    """Cria as formas de cada jogador a partir dos objetos recebidos do servidor."""
    shapes = []
    for player, value in received_objects.items():
        if player == "IoU":
            continue

        transparency = (
            255 if player == f"P{client_id}" else cfg.data["game"]["transparency"]
        )
        player_color = [*color.data[value["color"]], transparency]

        for count, obj in enumerate(value["pos"]):
            shapes.append(
                shape_classes[obj[-1]](
                    cfg, player, count, screen.screen, player_color, obj[:-1]
                )
            )

    return sorted(shapes, key=lambda obj: obj.id == client_id)


# --- Start State ---
shapes = initialize_objects(received_objects)
iou = received_objects["IoU"]


# --- Main loop ---
def start_game():
    global iou

    while screen.game_running:
        update = screen.game_loop(shapes, iou)
        send_new_position(client_socket, update)

        received = receive_new_position(client_socket)
        for shape in shapes[: -cfg.data["game"]["objectsNum"]]:
            shape.position = received[f"P{shape.id}"]["pos"][shape.obj_id][:-1]

        iou = received["IoU"]


# --- Main Entrance ---
if __name__ == "__main__":
    start_game()
