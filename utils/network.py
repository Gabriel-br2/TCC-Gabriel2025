import json
import socket
import time


def establish_client_connection(config):
    server_ip = config.data["server"]["ip"]
    port = config.data["server"]["port"]

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            client_socket.connect((server_ip, port))
            print("Cliente conectado ao servidor!")
            break

        except Exception as e:
            print(
                "Falha ao conectar ao servidor. Certifique-se de que ele está em execução e acessível."
            )

            print("Tentando novamente em 5 segundos...")
            time.sleep(5)
            continue

    initial_data = client_socket.recv(2048).decode("utf-8")
    print("Cliente - Dados iniciais recebidos")

    data = json.loads(initial_data)
    return client_socket, data["id"], data["objects"]


def send_new_position(client_socket, new_position):
    update_message = {"pos": new_position}
    client_socket.sendall(json.dumps(update_message).encode("utf-8"))


def receive_new_position(client_socket):
    data = client_socket.recv(2048).decode("utf-8")
    return json.loads(data)
