import socket
import json

def establish_client_connection(config):
    """
    Establishes a connection to the server.

    This function creates a socket, connects to the server specified in the config,
    receives initial data, and returns the socket, client ID, and initial object data.

    Args:
        config (YamlConfig): The configuration object containing server IP and port.

    Returns:
        tuple: A tuple containing the client socket, client ID, and initial objects data.
               Returns None if connection fails.
    """
    server_ip = config.data["server"]["ip"] 
    port = config.data["server"]["port"]

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((server_ip, port))
        print("Cliente conectado ao servidor!")

        initial_data = client_socket.recv(2048).decode('utf-8')
        print("Cliente - Dados iniciais recebidos")

        data = json.loads(initial_data)
        return client_socket, data["id"], data["objects"]

    except ConnectionRefusedError:
        print("Falha ao conectar ao servidor. Certifique-se de que ele está em execução e acessível.")
        return None


def send_new_position(client_socket, new_position):
    """
    Sends the new position to the server.

    Args:
        client_socket (socket): The client socket.
        new_position (dict): A dictionary containing the new position data.
    
    Returns:
        None
    """
    update_message = {"pos": new_position}
    client_socket.sendall(json.dumps(update_message).encode('utf-8'))

def receive_new_position(client_socket):
    """
    Receives updated position data from the server.

    Args:
        client_socket (socket): The client socket.

    Returns:
        dict: A dictionary containing the updated position data.
    """
    data = client_socket.recv(2048).decode('utf-8')
    return json.loads(data)