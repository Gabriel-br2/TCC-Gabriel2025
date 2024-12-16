import json
import random
import socket
from _thread import *

from utils.config import ConfigYaml

cfg   = ConfigYaml("config")
cfg.read_config()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = cfg.data["server"]["ip"]
port = cfg.data["server"]["port"]

server_ip = socket.gethostbyname(server)

try:
    s.bind((server, port))

except socket.error as e:
    print(str(e))

s.listen(cfg.data["game"]["playerNum"])
print("Waiting for a connection ...")

# Generate Objects
Objects = {}
player_Color = ["red", "green", "blue", "pink"]
for i in range(cfg.data["game"]["playerNum"]):
    objectPosition = []
    for o in range(cfg.data["game"]["objectsNum"] + 1):
        x = random.randint(10,cfg.data["screen"]["width"])
        y = random.randint(10,cfg.data["screen"]["height"])

        objectPosition.append([x,y])

    Objects[f"P{i}"] = {"id":i, "color": player_Color[i], "pos": objectPosition}

clients = []
def broadcast(data, sender_conn=None):
    for conn in clients:
        if conn != sender_conn:
            try:
                conn.sendall(data)
            except:
                clients.remove(conn)

def threaded_client(conn, player_id):
    global Objects

    try:
        initial_message = {
            "id": player_id,
            "objects": Objects
        }

        conn.sendall(json.dumps(initial_message).encode('utf-8'))

        while True:
            try:
                data = conn.recv(2048)
                reply = data.decode('utf-8')

                #print(player_id, reply)

                if not data:
                    conn.send(str.encode("Goodbye"))
                    break
                
                try:
                    update = json.loads(data.decode('utf-8'))
                    player_key = f"P{player_id}"
                    Objects[player_key]["pos"] = update["pos"]

                    message = json.dumps(Objects)

                    print("BBBBBBBBBBBBBBB", message)

                    broadcast(message.encode('utf-8'), sender_conn=conn)

                except json.JSONDecodeError:
                    print("Erro ao decodificar mensagem do cliente.")

            except:
                break

    except Exception as e:
        print(f"Erro com cliente {player_id}: {e}")
    finally:
        print(f"Cliente {player_id} desconectado.")
        clients.remove(conn)
        conn.close()

    print("Connection Closed")
    conn.close()

player_id = 0
while True:
    conn, addr = s.accept()
    print(f"Conexão estabelecida com {addr}")
    clients.append(conn)

    start_new_thread(threaded_client, (conn, player_id))
    player_id += 1

    if player_id >= cfg.data["game"]["playerNum"]:
        print("Número máximo de jogadores conectados.")