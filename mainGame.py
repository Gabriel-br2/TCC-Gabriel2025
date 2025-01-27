import random

from screen import screen
from utils.config import ConfigYaml
from utils.network import *

from player.linguisticModel import LLM_Player
from player.human import human_Player

from objects.generic import generic 
from objects.teewee import teewee 

cfg   = ConfigYaml("config")
color = ConfigYaml("color")

cfg.read_config()
color.read_config()

def teste(key):
    sc.screenshot_Base64(True)
    print(key)

# RECEBER Figuras
client_socket, ClientId, objects_recev = client_conn(cfg)

sc = screen(cfg.data, color.data, teste, ClientId, objects_recev[f"P{ClientId}"]["color"])

objects = {}

objects["teewee"]      =       teewee(sc.screen, color.data["white"], (0,0), cfg.data['game']['objectBaseSquareTam'])
objects["generic"]     =      generic(sc.screen, color.data["white"], (0,0), cfg.data['game']['objectBaseSquareTam'])
objects["humanPlayer"] = human_Player(sc.screen, color.data["white"], (0,0) ,cfg.data['game']['playerTam'])

obj = objects_recev[f"P{ClientId}"]
objects[f"me"] = [human_Player(sc.screen, color.data[obj["color"]], obj["pos"][0][:2] ,cfg.data['game']['playerTam'], sc.space)]

for k in objects_recev[f"P{ClientId}"]["pos"][1:]:
    x,y = k[:2]

    if k[3] == "generic":
        objects[f"me"].append(generic(sc.screen, color.data[obj["color"]], (x,y), cfg.data['game']['objectBaseSquareTam'], sc.space))
    
    if k[3] == "teewee":
        objects[f"me"].append(teewee(sc.screen, color.data[obj["color"]], (x,y), cfg.data['game']['objectBaseSquareTam'], sc.space))


objects["you"] = {}
for i in range(cfg.data['game']['playerNum']):
    if ClientId != i:
        objects[f"you"][f"P{i}"] = {"color": objects_recev[f"P{i}"]["color"], "pos": objects_recev[f"P{i}"]["pos"]}


def mainGame():
    global ClientId
    iou = objects_recev["IoU"]
    while sc.GameRunning:
        sc.screen_LoopGame(setNewPosition, getNewPosition, client_socket, objects, ClientId, iou)

def mainMenu():
    while sc.MenuRunning:
        sc.screen_MenuLoop()

if __name__ == "__main__":
    mainGame()