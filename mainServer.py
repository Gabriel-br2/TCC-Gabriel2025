import json
import random
import socket
from _thread import start_new_thread

from utils.config import YamlConfig
from utils.objective import *
from player.human import HumanPlayer
from objects.generic import GenericShape
from objects.TShape import TeeweeShape

cfg = YamlConfig("config")
cfg.read_config()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = socket.gethostbyname(cfg.data["server"]["ip"])
server_port = cfg.data["server"]["port"]

try:
    server_socket.bind((server_ip, server_port))
except socket.error as e:
    print(f"Erro ao vincular o servidor: {e}")

server_socket.listen(cfg.data["game"]["playerNum"])
print("Aguardando conexão...")

generic_model = GenericShape(None, None, (0, 0), cfg.data['game']['objectBaseSquareTam'])
teewee_model = TeeweeShape(None, None, (0, 0), cfg.data['game']['objectBaseSquareTam'])

player_colors = ["red", "green", "blue", "pink"]
objects = {}

for i in range(cfg.data["game"]["playerNum"]):
    object_options = ["HumanPlayer", "generic", "teewee"]
    object_positions = []

    for o in range(cfg.data["game"]["objectsNum"] + 1):
        x = random.randint(10, cfg.data["screen"]["width"])
        y = random.randint(10, cfg.data["screen"]["height"])
        obj = random.choice(object_options) if o != 0 else "HumanPlayer"
        object_options.remove(obj)

        # Adicionar posição e tipo de objeto
        object_positions.append([x, y, 0, obj])

    objects[f"P{i}"] = {"id": i, "color": player_colors[i], "pos": object_positions}

objects["IoU"] = 0
models = {"generic": generic_model.vertices, "teewee": teewee_model.vertices}

goal_area = calculate_goal_area(models)
clients = []

def broadcast(data, target_conn=None):
    if target_conn:
        try:
            target_conn.sendall(data)
        except Exception as e:
            print(f"Erro ao enviar mensagem para o cliente: {e}")
            if target_conn in clients:
                clients.remove(target_conn)

def handle_client_connection(conn, player_id):
    global objects

    try:
        initial_message = {
            "objects": objects,
            "id": player_id
        }

        conn.sendall(json.dumps(initial_message).encode('utf-8'))

        while True:
            try:
                data = conn.recv(2048)
                if not data:
                    conn.send(str.encode("Goodbye"))
                    break

                update = json.loads(data.decode('utf-8'))
                player_key = f"P{player_id}"
                objects[player_key]["pos"] = update["pos"]

                data_reorganized = reorganize_data(objects, models)
                objects["IoU"] = calculate_progress(cfg.data["game"]["playerNum"], goal_area, calculate_union_area(data_reorganized))

                message = json.dumps(objects)
                broadcast(message.encode('utf-8'), target_conn=conn)

            except json.JSONDecodeError:
                print("Erro ao decodificar a mensagem do cliente.")
    except Exception as e:
        print(f"Erro com cliente {player_id}: {e}")
    finally:
        print(f"Cliente {player_id} desconectado.")
        clients.remove(conn)
        conn.close()

player_id = 0
while True:
    conn, addr = server_socket.accept()
    print(f"Conexão estabelecida com {addr}")

    if player_id >= cfg.data["game"]["playerNum"]:
        print("Número máximo de jogadores conectados.")
        conn.close()
    else:
        clients.append(conn)
        start_new_thread(handle_client_connection, (conn, player_id))
        player_id += 1
