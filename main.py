import random

from screen import screen
from utils.config import ConfigYaml

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

sc = screen(cfg.data, color.data, teste)

objects = {"P0":[human_Player(sc.screen, sc.space[0], color.data["red"], 25)]}

# RECEBER OBJETOS

# test
for i in range(2):
    x = random.randint(100,700)
    y = random.randint(100,500)

    objects["P0"].append(generic(sc.screen, sc.space[0], color.data["red"], 50, (x,y)))

while sc.running:
    sc.screen_Loop(objects)