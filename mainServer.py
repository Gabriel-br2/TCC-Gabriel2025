#!/usr/bin/env python3
import json
import logging
import os
import random
import socket
import time
from _thread import start_new_thread
from threading import Lock

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
cycle_id = 0
data_lock = Lock()


def place_object(obj_type, existing_positions, max_attempts=100):
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
    global cycle_id
    cycle_id += 1
    logging.info(f"Generating a new cycle... (ID: {cycle_id})")

    chosen_objects = random.choices(object_options, k=num_objects)
    new_objects = {}
    for pid in range(num_players):
        positions = []
        for obj in chosen_objects:
            placed = place_object(obj, positions)
            if placed:
                positions.append(placed)
        new_objects[f"P{pid}"] = {
            "id": pid,
            "color": player_colors[pid],
            "pos": [p[:4] for p in positions],
        }
    new_objects["IoU"] = 0
    new_objects["cycle_id"] = cycle_id
    new_goal_area = calculate_goal_area([modelsClass[o] for o in chosen_objects])
    return new_objects, new_goal_area


def broadcast(data, client_list):
    disconnected_clients = []
    for client_conn in client_list:
        try:
            client_conn.sendall(data)
        except Exception as e:
            logging.error(f"Error broadcasting to a client: {e}")
            disconnected_clients.append(client_conn)

    if disconnected_clients:
        with data_lock:
            for client in disconnected_clients:
                if client in clients:
                    clients.remove(client)


def handle_server_calc():
    global objects, goal_area
    while True:
        if len(clients) == num_players:
            data_to_send = None
            client_list_copy = []

            with data_lock:
                reset_cycle = False
                reorganized = reorganize_data(objects, modelsClass)
                union_area = calculate_union_area(reorganized)
                progress = calculate_progress(num_players, goal_area, union_area)
                objects["IoU"] = progress

                if progress >= 0.95:
                    logging.info(
                        f"Objective reached with {progress:.2f}%! Resetting cycle."
                    )
                    objects, goal_area = generate_cycle()
                    reset_cycle = True

                data_to_send = json.dumps(
                    {"objects": objects, "reset": reset_cycle}
                ).encode("utf-8")
                client_list_copy = clients[:]

            if data_to_send and client_list_copy:
                broadcast(data_to_send, client_list_copy)

        time.sleep(0.25)


def handle_client_connection(conn, player_id):
    global objects, cycle_id
    try:
        with data_lock:
            initial_data = {"objects": objects, "id": player_id, "reset": False}
            conn.sendall(json.dumps(initial_data).encode("utf-8"))

        while True:
            data = conn.recv(2048)
            if not data:
                break

            try:
                update = json.loads(data.decode("utf-8"))
                player_key = f"P{player_id}"

                update_cycle_id = update.get("cycle_id")

                with data_lock:
                    if update_cycle_id == cycle_id:
                        if player_key in objects:
                            objects[player_key]["pos"] = update["pos"]
                    else:
                        pass
            except json.JSONDecodeError:
                pass

    except Exception as e:
        logging.error(f"Client {player_id} error: {e}")
    finally:
        logging.info(f"Client {player_id} disconnected.")
        with data_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()


# --- main Loop ---
if __name__ == "__main__":
    objects, goal_area = generate_cycle()
    player_id = 0

    start_new_thread(handle_server_calc, ())

    logging.info("Server started. Waiting for connections...")
    while player_id < num_players:
        conn, addr = server_socket.accept()
        logging.info(f"Connection established with {addr}")

        with data_lock:
            clients.append(conn)
        start_new_thread(handle_client_connection, (conn, player_id))
        player_id += 1

    logging.warning("Max players reached. No longer accepting connections.")
    while True:
        time.sleep(60)
