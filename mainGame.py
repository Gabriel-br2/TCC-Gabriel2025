import random

from screen import screen
from utils.config import ConfigYaml
from utils.network import *

from player.linguisticModel import LLM_Player
from player.human import human_Player
from objects.generic import generic 

cfg   = ConfigYaml("config")
color = ConfigYaml("color")

cfg.read_config()
color.read_config()

def teste(key):
    sc.screenshot_Base64(True)
    print(key)

# RECEBER Figuras
client_socket, ClientId, objects_recev = client_conn(cfg)

sc = screen(cfg.data, color.data, teste, ClientId)

objects = {}
for i in range(cfg.data["game"]["playerNum"]):
    print(objects_recev[f"P{i}"])

    obj = objects_recev[f"P{i}"]
    objects[f"P{i}"] = [human_Player(sc.screen, sc.space[i], color.data[obj["color"]], obj["pos"][0] ,25)]

    for k in objects_recev[f"P{i}"]["pos"][1:]:
        x,y = k
        objects[f"P{i}"].append(generic(sc.screen, sc.space[i], color.data[objects_recev[f"P{i}"]["color"]], 50, (x,y)))

def mainGame():
    global ClientId
    while sc.GameRunning:
        sc.screen_LoopGame(setNewPosition, getNewPosition, client_socket, objects, ClientId)

def mainMenu():
    while sc.MenuRunning:
        sc.screen_MenuLoop()

if __name__ == "__main__":
    mainGame()
    