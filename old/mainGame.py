import sys

from player.human import HumanPlayer
from player.linguisticModel import LLM_Player

from objects.generic import GenericShape
from objects.TShape import TeeweeShape
from screen import Screen
from utils.config import YamlConfig
from utils.network import *

# Load configuration from YAML file.
cfg = YamlConfig("config")
color = YamlConfig("color")

cfg.read_config()
color.read_config()

playerType = sys.argv[1] if len(sys.argv) > 1 else "human"


def capture_screenshot(key):
    """
    Captures a screenshot and prints a key (currently unused).

    Args:
        key: The key pressed (currently unused).

    Returns:
        None
    """
    sc.screenshot_Base64(True)  # Capture screenshot as Base64.
    print(key)


# Establish connection with the server and receive initial data.
client_socket, client_id, received_objects = establish_client_connection(cfg)

# Initialize the screen and game environment.
sc = Screen(
    cfg.data,
    color.data,
    capture_screenshot,
    client_id,
    received_objects[f"P{client_id}"]["color"],
)

# Dictionary to store game objects.
objects = {}

# Initialize object models (used for shape definitions).
objects["teewee"] = TeeweeShape(sc.screen, color.data["white"], (0, 0), cfg)
objects["generic"] = GenericShape(sc.screen, color.data["white"], (0, 0), cfg)
objects["HumanPlayer"] = HumanPlayer(sc.screen, color.data["white"], (0, 0), cfg)
objects["llmPlayer"] = LLM_Player(sc.screen, color.data["white"], (0, 0), cfg)

# Initialize the player's objects.
player_obj = received_objects[f"P{client_id}"]

if playerType == "human":
    objects["me"] = [
        HumanPlayer(
            sc.screen,
            color.data[player_obj["color"]],
            player_obj["pos"][0][:2],
            cfg,
            sc.space,
        )
    ]
elif playerType == "LLM":
    objects["me"] = [
        LLM_Player(
            sc.screen,
            color.data[player_obj["color"]],
            player_obj["pos"][0][:2],
            cfg,
            sc.space,
        )
    ]


# Create other objects owned by the player.
for position in player_obj["pos"][1:]:
    x, y = position[:2]

    if position[3] == "generic":
        objects["me"].append(
            GenericShape(
                sc.screen, color.data[player_obj["color"]], (x, y), cfg, sc.space
            )
        )

    elif position[3] == "teewee":
        objects["me"].append(
            TeeweeShape(
                sc.screen, color.data[player_obj["color"]], (x, y), cfg, sc.space
            )
        )

# Initialize objects for other players.
objects["you"] = {}
for i in range(cfg.data["game"]["playerNum"]):
    if client_id != i:
        objects["you"][f"P{i}"] = {
            "color": received_objects[f"P{i}"]["color"],
            "pos": received_objects[f"P{i}"]["pos"],
        }


def start_game():
    """
    Starts the main game loop.

    This function initializes the Intersection over Union (IoU) value and runs the game loop
    until the player quits.

    Returns:
        None
    """
    global client_id
    iou = received_objects["IoU"]  # Get initial IoU from the server

    while sc.game_running:
        sc.game_loop(
            send_new_position,
            receive_new_position,
            client_socket,
            objects,
            client_id,
            iou,
            playerType,
        )  # Run the game loop.


if __name__ == "__main__":
    start_game()  # Start the game.
