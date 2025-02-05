import json
import random
import socket
from _thread import *

from utils.config import ConfigYaml
from utils.objective import *

from player.human import human_Player
from objects.generic import generic 
from objects.TShape import teewee 

cfg   = ConfigYaml("config")
cfg.read_config()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

genericModel = generic(None, None, (0,0), cfg.data['game']['objectBaseSquareTam'])
teeweeModel  =  teewee(None, None, (0,0), cfg.data['game']['objectBaseSquareTam'])

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
    optionObjects = ["humanPlayer", "generic", "teewee"]
    objectPosition = []

    for o in range(cfg.data["game"]["objectsNum"] + 1):
        x = random.randint(10,cfg.data["screen"]["width"])
        y = random.randint(10,cfg.data["screen"]["height"])
        obj = random.choice(optionObjects) if o != 0 else "humanPlayer"
        optionObjects.remove(obj)

                             # x,  y, rz,  type
        objectPosition.append([x,  y,  0,  obj])

    Objects[f"P{i}"] = {"id":i, "color": player_Color[i], "pos": objectPosition}

Objects["IoU"] = 0

Models = {"generic": genericModel.vertices, "teewee": teeweeModel.vertices}


resultado = [sublista[3] for sublista in Objects["P0"]["pos"][1:]]
print("resultado:", resultado)

A_goal = calcA_Goal(Models)

clients = []
def broadcast(data, target_conn=None):
    if target_conn:
        try:
            target_conn.sendall(data)
        except Exception as e:
            print(f"Erro ao enviar mensagem para o cliente: {e}")
            if target_conn in clients:
                clients.remove(target_conn)

def threaded_client(conn, player_id):
    global Objects
    
    try:
        initial_message = {
            "objects": Objects,
            "id"     : player_id
        }

        conn.sendall(json.dumps(initial_message).encode('utf-8'))

        while True:
            try:
                data = conn.recv(2048)
                reply = data.decode('utf-8')

                if not data:
                    conn.send(str.encode("Goodbye"))
                    break
                
                try:
                    update = json.loads(data.decode('utf-8'))
                    player_key = f"P{player_id}"
                    Objects[player_key]["pos"] = update["pos"]

                    # calc objective
                    d = reorganizationData(Objects, Models)
                    Objects["IoU"] = calcPercentage(cfg.data["game"]["playerNum"], A_goal, calcUnion(d))

                    message = json.dumps(Objects)

                    broadcast(message.encode('utf-8'), target_conn=conn)

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

player_id = 0
while True:
    conn, addr = s.accept()
    print(f"Conexão estabelecida com {addr}")

    if player_id >= cfg.data["game"]["playerNum"]:
        print("Número máximo de jogadores conectados.")
        conn.close()

    else:
        clients.append(conn)
        start_new_thread(threaded_client, (conn, player_id))
        player_id += 1

    