import json
import socket
import time


def establish_client_connection(config, nature):
    """
    Tenta estabelecer uma conexão com o servidor.
    Retorna os dados da conexão em caso de sucesso ou None em caso de falha.
    """
    server_ip = config.data["server"]["ip"]
    port = config.data["server"]["port"]
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Define um timeout curto para a tentativa de conexão não bloquear o programa
    client_socket.settimeout(2)

    try:
        print(f"Tentando conectar a {server_ip}:{port}...")
        client_socket.connect((server_ip, port))
        print("Cliente conectado ao servidor!")

        # Envia a 'natureza' do jogador (human/LLM)
        update_message = {"nature": nature}
        client_socket.sendall(json.dumps(update_message).encode("utf-8"))

        # Recebe os dados iniciais
        initial_data = client_socket.recv(4096).decode("utf-8")
        print("Cliente - Dados iniciais recebidos")
        data = json.loads(initial_data)

        # Retorna os dados da conexão bem-sucedida
        return client_socket, data["id"], data, data["timestamp"]

    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"Falha ao conectar ao servidor: {e}. Tentando novamente...")
        client_socket.close()
        return None


def send_new_position(client_socket, new_position, current_cycle_id):
    update_message = {"pos": new_position, "cycle_id": current_cycle_id}
    client_socket.sendall(json.dumps(update_message).encode("utf-8"))


def receive_new_position(client_socket):
    data = client_socket.recv(4096).decode("utf-8")
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        print("Erro ao decodificar os dados recebidos do servidor.")
        return json.loads("}".join(data.split("}")[:4]) + "}")
