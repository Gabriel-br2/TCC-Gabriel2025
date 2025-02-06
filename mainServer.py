import json
import random
import socket
from _thread import start_new_thread

from utils.config import YamlConfig
from utils.objective import *
from player.human import HumanPlayer
from objects.generic import GenericShape
from objects.TShape import TeeweeShape

# Load configuration from YAML file.
cfg = YamlConfig("config")
cfg.read_config()

# Initialize the server socket.
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = socket.gethostbyname(cfg.data["server"]["ip"])  # Get server IP from config
server_port = cfg.data["server"]["port"]  # Get server port from config

try:
    server_socket.bind((server_ip, server_port))  # Bind the socket to the IP and port
except socket.error as e:
    print(f"Error binding the server: {e}")

server_socket.listen(cfg.data["game"]["playerNum"])  # Listen for connections
print("Waiting for connection...")

# Initialize object models (used for shape definitions).
generic_model = GenericShape(None, None, (0, 0), cfg.data['game']['objectBaseSquareTam'])
teewee_model = TeeweeShape(None, None, (0, 0), cfg.data['game']['objectBaseSquareTam'])

# Define player colors.
player_colors = ["red", "green", "blue", "pink"]
# Dictionary to store objects' data (players and other objects).
objects = {}

# Initialize objects for each player.
for i in range(cfg.data["game"]["playerNum"]):
    object_options = ["HumanPlayer", "generic", "teewee"]  # Possible object types
    object_positions = []

    for o in range(cfg.data["game"]["objectsNum"] + 1):  # Create objects for each player (+1 for HumanPlayer).
        x = random.randint(10, cfg.data["screen"]["width"])  # Random x position
        y = random.randint(10, cfg.data["screen"]["height"])  # Random y position
        obj = random.choice(object_options) if o != 0 else "HumanPlayer"  # Randomly choose object type, or HumanPlayer if first object.
        object_options.remove(obj)  # Remove the chosen object type from the options.

        # Store object position, rotation, and type.
        object_positions.append([x, y, np.pi, obj])

    objects[f"P{i}"] = {"id": i, "color": player_colors[i], "pos": object_positions}  # Store object data for each player.

objects["IoU"] = 0  # Initialize Intersection over Union (IoU)
models = {"generic": generic_model.vertices, "teewee": teewee_model.vertices}  # Store model vertices for calculations.

goal_area = calculate_goal_area(models)  # Calculate the total goal area.
clients = []  # List to store connected clients' sockets.

def broadcast(data, target_conn=None):
    """
    Broadcasts data to all connected clients, except optionally to a specified client.

    Args:
        data (bytes): The data to send.
        target_conn (socket, optional): A specific client connection to send to. If provided, send only to this connection. Defaults to None.
    """
    if target_conn:
        try:
            target_conn.sendall(data) # send to a specific connection
        except Exception as e:
            print(f"Error sending message to client: {e}")
            if target_conn in clients:
                clients.remove(target_conn) # remove client if error

def handle_client_connection(conn, player_id):
    """
    Handles a single client connection in a separate thread.

    Args:
        conn (socket): The client's socket.
        player_id (int): The player's ID.
    """
    global objects

    try:
        # Send initial game data to the client.
        initial_message = {
            "objects": objects,
            "id": player_id
        }

        conn.sendall(json.dumps(initial_message).encode('utf-8'))

        while True:
            try:
                data = conn.recv(2048)  # Receive data from the client.
                if not data:  # If client disconnects.
                    conn.send(str.encode("Goodbye"))
                    break

                update = json.loads(data.decode('utf-8'))  # Decode the received JSON data.
                player_key = f"P{player_id}"
                objects[player_key]["pos"] = update["pos"]  # Update the player's position.

                # Recalculate IoU and broadcast updated game data to all clients.
                data_reorganized = reorganize_data(objects, models)
                objects["IoU"] = calculate_progress(cfg.data["game"]["playerNum"], goal_area, calculate_union_area(data_reorganized))

                message = json.dumps(objects)
                broadcast(message.encode('utf-8'), target_conn=conn) #send only to the client who sent the info

            except json.JSONDecodeError:
                print("Error decoding client message.")
    except Exception as e:
        print(f"Error with client {player_id}: {e}")
    finally:
        print(f"Client {player_id} disconnected.")
        clients.remove(conn)  # Remove client from the list
        conn.close()  # Close the connection.

player_id = 0
while True:
    conn, addr = server_socket.accept()  # Accept a new connection.
    print(f"Connection established with {addr}")

    if player_id >= cfg.data["game"]["playerNum"]:  # Check if maximum players reached.
        print("Maximum number of players connected.")
        conn.close()  # Close the connection.
    else:
        clients.append(conn)  # Add client to the list
        start_new_thread(handle_client_connection, (conn, player_id))  # Start a new thread for the client.
        player_id += 1  # Increment player ID.