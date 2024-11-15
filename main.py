from screen import screen
from utils.config import ConfigYaml

from player.human import human_Player
from objects.generic import generic 

cfg   = ConfigYaml("config")
cfg.read_config()

color = ConfigYaml("color")
color.read_config()

def teste(key):
    print(key)

sc = screen(cfg.data, color.data, teste)

objects = [human_Player(sc.screen, sc.space, color.data, 50),
           generic(sc.screen, sc.space, color.data, 50)]

while sc.running:
    sc.screen_Loop(objects)