#!/usr/bin/env python3
import argparse
import threading
import time

import pygame
from screen import Screen
from utils.config import YamlConfig
from dinamic_import import plugins_import
from utils.network import establish_client_connection
from utils.network import receive_new_position
from utils.network import send_new_position


# --- Variáveis Globais ---
latest_server_state = {}
state_lock = threading.Lock()
game_is_running = True
current_cycle_id = 0

# --- Leitura de Configurações ---
cfg = YamlConfig("config")
color = YamlConfig("color")
cfg.read_config()
color.read_config()

shape_classes = plugins_import("objects")
print(shape_classes)

screen = Screen(cfg.data, color.data, "human")

connection_data = None
attempt_count = 0
while screen.game_running and connection_data is None:
    if not screen.show_waiting_screen(attempt_count):
        game_is_running = False
        break

    connection_data = establish_client_connection(cfg, "human", screen.nameId)

    if connection_data is None:
        time.sleep(2)

    attempt_count += 1

if connection_data:
    client_socket, client_id, initial_data, timestamp = connection_data

    screen.setup_player_specifics(client_id, timestamp, None)

    received_objects = initial_data["objects"]
    current_cycle_id = received_objects.get("cycle_id", 0)
    shape_classes = plugins_import("objects")

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
                    shape_classes[obj[-1]](
                        cfg,
                        int(player[1:]),
                        count,
                        screen.screen,
                        player_color,
                        obj[:-1],
                    )
                )
        return sorted(shapes, key=lambda s: (s.id != client_id, s.id, s.obj_id))

    def network_listener(sock):
        global latest_server_state, game_is_running

        while game_is_running:
            server_update = receive_new_position(sock)

            # Caso 1: Timeout (Servidor quieto, esperando P2, etc.)
            # Apenas ignore e tente ler de novo no próximo loop.
            if server_update is None:
                continue  # <-- Esta é a mudança principal

            # Caso 2: Erro real (Desconexão, etc.)
            # Agora verificamos se é um dict e se tem a chave "error"
            if isinstance(server_update, dict) and "error" in server_update:
                print(
                    f"Erro na conexão com o servidor: {server_update['error']}. Encerrando o jogo."
                )
                game_is_running = False
                break

            # Caso 3: Dados válidos recebidos
            # Se não for None e não for um erro, são dados do jogo.
            with state_lock:
                latest_server_state = server_update

    shapes = initialize_objects(received_objects)
    iou = received_objects.get("IoU", 0)

    def start_game():
        global iou, shapes, latest_server_state, game_is_running, current_cycle_id

        listener_thread = threading.Thread(
            target=network_listener, args=(client_socket,), daemon=True
        )
        listener_thread.start()

        c = 0
        while screen.game_running and game_is_running:
            c += 1
            update_payload = screen.game_loop(shapes, iou)

            if c == 1 or (c % 75) == 0:
                if update_payload:
                    send_new_position(client_socket, update_payload, current_cycle_id)

            current_update = None
            with state_lock:
                if latest_server_state:
                    current_update = latest_server_state
                    latest_server_state = {}

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

screen.close()
print("Programa encerrado.")
