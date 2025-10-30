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

    # Define um timeout curto para a tentativa de CONEXÃO
    client_socket.settimeout(2.0)  # 2 segundos

    try:
        print(f"Tentando conectar a {server_ip}:{port}...")
        client_socket.connect((server_ip, port))
        print("Cliente conectado ao servidor!")

        # --- Alteração ---
        # Define um timeout para operações normais de RECV (recebimento)
        # 10 segundos é um bom valor de espera.
        client_socket.settimeout(10.0)

        # Envia a 'natureza' do jogador (human/LLM)
        update_message = {"nature": nature}
        client_socket.sendall(json.dumps(update_message).encode("utf-8"))

        # Recebe os dados iniciais
        initial_data = client_socket.recv(4096).decode("utf-8")
        print("Cliente - Dados iniciais recebidos")
        data = json.loads(initial_data)

        # Retorna os dados da conexão bem-sucedida
        return client_socket, data["id"], data, data["timestamp"]

    except socket.timeout:
        # Pega o timeout da conexão (2s) ou do recv inicial (10s)
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
    """
    Tenta receber dados do servidor.
    Retorna None em caso de timeout.
    Retorna {"error": "..."} em caso de desconexão ou erro grave.
    """
    try:
        # Esta linha irá falhar com socket.timeout após 10s (definido acima)
        data = client_socket.recv(4096).decode("utf-8")

        if not data:
            # Se 'data' for vazio, o servidor fechou a conexão
            print("Servidor fechou a conexão.")
            return {"error": "disconnected"}

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            print("Erro ao decodificar os dados recebidos do servidor.")
            # Mantendo sua lógica original de fallback para JSON malformado
            return json.loads("}".join(data.split("}")[:4]) + "}")

    except socket.timeout:
        # --- ESTA É A CORREÇÃO PRINCIPAL ---
        # Ocorreu um timeout, o que é esperado se o servidor estiver
        # esperando por outros jogadores. Retornamos None para que
        # o loop no mainGame.py possa continuar sem crashar.
        return None

    except Exception as e:
        # Outro erro (ex: Conexão resetada)
        print(f"Erro ao receber dados: {e}")
        return {"error": str(e)}
