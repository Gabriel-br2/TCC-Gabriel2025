import json
import socket
import time


def establish_client_connection(config, nature, name=None):
    server_ip = config.data["server"]["ip"]
    port = config.data["server"]["port"]
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.settimeout(2.0)

    try:
        print(f"Tentando conectar a {server_ip}:{port}...")
        client_socket.connect((server_ip, port))
        print("Cliente conectado ao servidor!")

        client_socket.settimeout(10.0)

        update_message = {"nature": nature, "name": name}
        client_socket.sendall(json.dumps(update_message).encode("utf-8"))

        initial_data = client_socket.recv(4096).decode("utf-8")
        print("Cliente - Dados iniciais recebidos")
        data = json.loads(initial_data)

        return client_socket, data["id"], data, data["timestamp"]

    except socket.timeout:
        print(f"A operação excedeu o tempo limite (timeout).")
        client_socket.close()
        return None
    except (ConnectionRefusedError, OSError) as e:
        print(f"Falha ao conectar ao servidor: {e}. Tentando novamente...")
        client_socket.close()
        return None


def send_new_position(client_socket, new_position, current_cycle_id):
    try:
        update_message = {"pos": new_position, "cycle_id": current_cycle_id}
        client_socket.sendall(json.dumps(update_message).encode("utf-8"))
    except Exception as e:
        print(f"Erro ao enviar posição: {e}")


def receive_new_position(client_socket):
    try:
        data = client_socket.recv(4096).decode("utf-8")

        if not data:
            print("Servidor fechou a conexão.")
            return {"error": "disconnected"}

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            print("Erro ao decodificar os dados recebidos do servidor.")
            return json.loads("}".join(data.split("}")[:4]) + "}")

    except socket.timeout:
        return None

    except Exception as e:
        print(f"Erro ao receber dados: {e}")
        return {"error": str(e)}
