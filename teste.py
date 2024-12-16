import socket
import json
import time
import random

def client_program(player_id):
    server_ip = "localhost" 
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((server_ip, port))
        print(f"Cliente {player_id} conectado ao servidor!")

        initial_data = client_socket.recv(2048).decode('utf-8')
        print(f"Cliente {player_id} - Dados iniciais recebidos: {initial_data}")

        while True:
            new_position = [{"x": random.randint(0, 500), "y": random.randint(0, 500)} for _ in range(5)]
            update_message = {"pos": new_position}

            client_socket.sendall(json.dumps(update_message).encode('utf-8'))
            print(f"Cliente {player_id} enviou: {update_message}")

            try:
                server_message = client_socket.recv(2048).decode('utf-8')
                print(f"Cliente {player_id} recebeu: {server_message}")
            except socket.error:
                print(f"Cliente {player_id} - Erro ao receber dados do servidor.")
                break

            time.sleep(2)

    except ConnectionRefusedError:
        print("Falha ao conectar ao servidor. Certifique-se de que ele está em execução e acessível.")

    except Exception as e:
        print(f"Erro inesperado no cliente {player_id}: {e}")

    finally:
        client_socket.close()
        print(f"Cliente {player_id} desconectado.")

# Testar chamando 4 vezes o cliente
if __name__ == "__main__":
    from multiprocessing import Process

    processes = []
    for i in range(4):  # Criar 4 clientes
        p = Process(target=client_program, args=(i,))
        p.start()
        processes.append(p)

    # Aguardar todos os processos terminarem
    for p in processes:
        p.join()
