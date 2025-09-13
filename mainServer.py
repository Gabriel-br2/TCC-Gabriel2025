#!/usr/bin/env python3
import json
import logging
import os
import random
import socket
import time
from _thread import start_new_thread

from objects.generic import GenericShape
from objects.teewee import TeeweeShape
from utils.colision import *
from utils.config import YamlConfig
from utils.objective import *

# --- Config ---
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

cfg = YamlConfig("config")
cfg.read_config()

player_colors = ["red", "green", "blue", "pink"]

num_objects = cfg.data["game"]["objectsNum"]
num_players = cfg.data["game"]["playerNum"]
screen_width = cfg.data["screen"]["width"]
screen_height = cfg.data["screen"]["height"]

# --- Socket ---
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = socket.gethostbyname(cfg.data["server"]["ip"])
server_port = cfg.data["server"]["port"]
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((server_ip, server_port))
server_socket.listen(num_players)

# --- Object ---
object_options = [
    f.split(".")[0]
    for f in os.listdir("objects")
    if os.path.isfile(os.path.join("objects", f))
]

modelsClass = {
    "generic": GenericShape(cfg).vertices,
    "teewee": TeeweeShape(cfg).vertices,
}

clients = []
objects, goal_area = {}, None


# --- aux Function ---
def place_object(obj_type, existing_positions, max_attempts=100):
    """Tenta posicionar um objeto sem colisão dentro da tela."""
    model_vertices = modelsClass[obj_type]
    for _ in range(max_attempts):
        x, y = random.randint(0, screen_width), random.randint(0, screen_height)
        rotation = random.choice([0, 90, 180, 270])
        transformed = apply_transformation(x, y, rotation, model_vertices)
        aabb = get_axis_aligned_bounding_box(transformed)
        if not any(
            aabbs_intersect(aabb, other_aabb) for *_, other_aabb in existing_positions
        ):
            return [x, y, rotation, obj_type, aabb]
    return None


def generate_cycle():
    chosen_objects = random.choices(object_options, k=num_objects)
    objects = {}
    for pid in range(num_players):
        positions = []
        for obj in chosen_objects:
            placed = place_object(obj, positions)
            if placed:
                positions.append(placed)
        objects[f"P{pid}"] = {
            "id": pid,
            "color": player_colors[pid],
            "pos": [p[:4] for p in positions],
        }
    objects["IoU"] = 0
    goal_area = calculate_goal_area([modelsClass[o] for o in chosen_objects])
    return objects, goal_area


def broadcast(data, target_conn=None):
    if target_conn:
        try:
            target_conn.sendall(data)
        except Exception as e:
            logging.error(f"Error sending to client: {e}")
            if target_conn in clients:
                clients.remove(target_conn)

def handle_server_calc():
    global objects, goal_area
    while True:
        if len(clients) == num_players:
            reorganized = reorganize_data(objects, modelsClass)
            progress = calculate_progress(
                num_players, goal_area, calculate_union_area(reorganized)
            )
            objects["IoU"] = progress
        time.sleep(0.25)


def handle_client_connection(conn, player_id):
    global objects, goal_area
    try:
        conn.sendall(json.dumps({"objects": objects, "id": player_id}).encode("utf-8"))
        while True:
            data = conn.recv(2048)
            if not data:
                break

            try:
                update = json.loads(data.decode("utf-8"))
                player_key = f"P{player_id}"
                objects[player_key]["pos"] = update["pos"]
                broadcast(json.dumps(objects).encode("utf-8"), target_conn=conn)
                
            except json.JSONDecodeError:
                logging.warning("Invalid JSON from client.")
    except Exception as e:
        logging.error(f"Client {player_id} error: {e}")
    finally:
        logging.info(f"Client {player_id} disconnected.")
        if conn in clients:
            clients.remove(conn)
        conn.close()


# --- main Loop ---
if __name__ == "__main__":
    logging.info("Server started. Waiting for connections...")
    objects, goal_area = generate_cycle()
    player_id = 0

    start_new_thread(handle_server_calc, ())

    while True:
        conn, addr = server_socket.accept()
        logging.info(f"Connection established with {addr}")

        clients.append(conn)
        start_new_thread(handle_client_connection, (conn, player_id))
        player_id += 1

        #if player_id == num_players:
        #    logging.warning("Max players reached, rejecting connection.")
        #    break
        