import socket
import json

def client_conn():
    server_ip = "localhost" 
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((server_ip, port))
        print(f"Cliente conectado ao servidor!")

        initial_data = client_socket.recv(2048).decode('utf-8')
        print(f"Cliente - Dados iniciais recebidos")

        data = json.loads(initial_data)
        return client_socket, data["id"], data["objects"]

    except ConnectionRefusedError:
        print("Falha ao conectar ao servidor. Certifique-se de que ele está em execução e acessível.")
    

def setNewPosition(client_socket, new_position):
    update_message = {"pos": new_position}

    client_socket.sendall(json.dumps(update_message).encode('utf-8'))
    print(f"Cliente enviou: {update_message}")

def getNewPosition(client_socket):
    data = client_socket.recv(2048).decode('utf-8')
    print("AAAAAAAAAAAAAAAAAAAA",data)
    data = json.loads(data)
    
    print(f"Cliente - Dados recebidos", data)
    return data

