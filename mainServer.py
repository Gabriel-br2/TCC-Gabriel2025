import json
import os
import random
import socket
from _thread import start_new_thread

from objects.generic import GenericShape
from objects.teewee import TeeweeShape
from utils.colision import *
from utils.config import YamlConfig
from utils.objective import *

cfg = YamlConfig("config")
cfg.read_config()

player_colors = ["red", "green", "blue", "pink"]

num_objects = cfg.data["game"]["objectsNum"]
num_players = cfg.data["game"]["playerNum"]
screen_width = cfg.data["screen"]["width"]
screen_height = cfg.data["screen"]["height"]

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = socket.gethostbyname(cfg.data["server"]["ip"])
server_port = cfg.data["server"]["port"]

server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((server_ip, server_port))

server_socket.listen(num_players)

object_options = [
    f.split(".")[0]
    for f in os.listdir("objects")
    if os.path.isfile(os.path.join("objects", f))
]

modelsClass = {
    "generic": GenericShape(cfg).vertices,
    "teewee": TeeweeShape(cfg).vertices,
}


def generate_cycle():
    global modelsClass, num_objects, num_players, screen_width, screen_height

    objChoice = random.choices(object_options, k=num_objects)

    objects = {}
    for i in range(num_players):
        object_positions = []

        for o in range(num_objects):
            for attempt in range(100):
                x = random.randint(0, screen_width)
                y = random.randint(0, screen_height)
                rz = random.choice([p * 90 for p in range(4)])

                current_transformed_vertices = apply_transformation(
                    x, y, rz, modelsClass[objChoice[o]]
                )
                current_aabb = get_axis_aligned_bounding_box(
                    current_transformed_vertices
                )

                has_intersection = False
                for _, _, _, _, other_aabb in object_positions:
                    if aabbs_intersect(current_aabb, other_aabb):
                        has_intersection = True
                        break

                if not has_intersection:
                    object_positions.append([x, y, rz, objChoice[o], current_aabb])
                    placed_successfully = True
                    break

        objects[f"P{i}"] = {
            "id": i,
            "color": player_colors[i],
            "pos": [data[:4] for data in object_positions],
        }

    objects["IoU"] = 0

    models = [modelsClass[o] for o in objChoice]
    goal_area = calculate_goal_area(models)

    return objects, goal_area


clients = []
print("Waiting for connection...")

objects, goal_area = generate_cycle()


def broadcast(data, target_conn=None):
    if target_conn:
        try:
            target_conn.sendall(data)

        except Exception as e:
            print(f"Error sending message to client: {e}")

            if target_conn in clients:
                clients.remove(target_conn)


def handle_client_connection(conn, player_id):
    try:
        initial_message = {"objects": objects, "id": player_id}

        conn.sendall(json.dumps(initial_message).encode("utf-8"))

        while True:
            try:
                data = conn.recv(2048)

                if not data:
                    conn.send(str.encode("Goodbye"))
                    break

                update = json.loads(data.decode("utf-8"))
                player_key = f"P{player_id}"
                objects[player_key]["pos"] = update[
                    "pos"
                ]  # Update the player's position.

                data_reorganized = reorganize_data(objects, modelsClass)
                c = calculate_progress(
                    cfg.data["game"]["playerNum"],
                    goal_area,
                    calculate_union_area(data_reorganized),
                )
                objects["IoU"] = c

                message = json.dumps(objects)
                broadcast(message.encode("utf-8"), target_conn=conn)

            except json.JSONDecodeError:
                print("Error decoding client message.")

    except Exception as e:
        print(f"Error with client {player_id}: {e}")

    finally:
        print(f"Client {player_id} disconnected.")
        clients.remove(conn)
        conn.close()


player_id = 0
while True:
    conn, addr = server_socket.accept()
    print(f"Connection established with {addr}")

    if player_id >= cfg.data["game"]["playerNum"] + 1:
        print("Maximum number of players connected.")
        conn.close()

    else:
        clients.append(conn)
        start_new_thread(handle_client_connection, (conn, player_id))
        player_id += 1
