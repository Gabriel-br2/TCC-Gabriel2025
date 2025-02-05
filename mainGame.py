from screen import Screen
from utils.config import YamlConfig
from utils.network import *
from player.human import HumanPlayer
from objects.generic import GenericShape
from objects.TShape import TeeweeShape 

cfg = YamlConfig("config")
color = YamlConfig("color")

cfg.read_config()
color.read_config()

def capture_screenshot(key):
    sc.screenshot_Base64(True)
    print(key)

client_socket, client_id, received_objects = establish_client_connection(cfg)
sc = Screen(cfg.data, color.data, capture_screenshot, client_id, received_objects[f"P{client_id}"]["color"])

objects = {}

objects["teewee"] = TeeweeShape(sc.screen, color.data["white"], (0, 0), cfg.data['game']['objectBaseSquareTam'])
objects["generic"] = GenericShape(sc.screen, color.data["white"], (0, 0), cfg.data['game']['objectBaseSquareTam'])
objects["HumanPlayer"] = HumanPlayer(sc.screen, color.data["white"], (0, 0), cfg.data['game']['playerTam'])

player_obj = received_objects[f"P{client_id}"]
objects["me"] = [HumanPlayer(sc.screen, color.data[player_obj["color"]], player_obj["pos"][0][:2], cfg.data['game']['playerTam'], sc.space)]

for position in player_obj["pos"][1:]:
    x, y = position[:2]
    
    if position[3] == "generic":
        objects["me"].append(GenericShape(sc.screen, color.data[player_obj["color"]], (x, y), cfg.data['game']['objectBaseSquareTam'], sc.space))
    
    elif position[3] == "teewee":
        objects["me"].append(TeeweeShape(sc.screen, color.data[player_obj["color"]], (x, y), cfg.data['game']['objectBaseSquareTam'], sc.space))

objects["you"] = {}
for i in range(cfg.data['game']['playerNum']):
    if client_id != i:
        objects["you"][f"P{i}"] = {"color": received_objects[f"P{i}"]["color"], "pos": received_objects[f"P{i}"]["pos"]}

def start_game():
    global client_id
    iou = received_objects["IoU"]
    while sc.game_running:
        sc.game_loop(send_new_position, receive_new_position, client_socket, objects, client_id, iou)

if __name__ == "__main__":
    start_game()
