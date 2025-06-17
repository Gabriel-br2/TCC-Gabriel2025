from objects.generic import GenericShape
from objects.teewee import TeeweeShape
from screen import Screen
from utils.config import YamlConfig
from utils.network import *

cfg = YamlConfig("config")
color = YamlConfig("color")

cfg.read_config()
color.read_config()

# def capture_screenshot(key):
#    sc.screenshot_Base64(True)
#    print(key)

client_socket, client_id, received_objects = establish_client_connection(cfg)

shapeClass = {"generic": GenericShape, "teewee": TeeweeShape}

sc = Screen(cfg.data, color.data, client_id)

objects = []
for player, value in received_objects.items():
    if player == "IoU":
        continue

    transparency = (
        255 if player == f"P{client_id}" else cfg.data["game"]["transparency"]
    )
    color_player = [*color.data[value["color"]], transparency]

    count = 0
    for obj in value["pos"]:
        objects.append(
            shapeClass[obj[-1]](cfg, player, count, sc.screen, color_player, obj[:-1])
        )
        count += 1

objects = sorted(objects, key=lambda obj: obj.id == client_id)


iou = received_objects["IoU"]


def start_game():
    global client_id
    global iou

    while sc.game_running:
        update = sc.game_loop(objects, iou)
        send_new_position(client_socket, update)

        received = receive_new_position(client_socket)

        for o in objects[: -cfg.data["game"]["objectsNum"]]:
            o.position = received[f"P{o.id}"]["pos"][o.obj_id][:-1]
        iou = received["IoU"]


if __name__ == "__main__":
    start_game()
