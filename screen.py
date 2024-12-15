import pygame
import pymunk
import pymunk.pygame_util

import os
import sys
import shutil
import base64
import datetime

class screen:
    def __init__(self, config, color, clickCallback, debug=False):
        pygame.init()

        self.running       = True
        self.debug         = debug
        self.color         = color
        self.config        = config
        self.clickCallback = clickCallback

        self.screen_Height = config['screen']['height']
        self.screen_Width  = config['screen']['width']

        self.clock = pygame.time.Clock()

        self.space = []
        for gamer in range(config["game"]["playerNum"]):
            self.space.append(pymunk.Space())
            self.space[-1].gravity = (0, 0)

        self.FPS = 60

        self.screen = pygame.display.set_mode((self.screen_Width, self.screen_Height))
        pygame.display.set_caption(config['screen']['caption'])

    def screenshot_Base64(self, save=False, file_path='screenshot/'):
        now = datetime.datetime.now()
        name = now.strftime("%Y%m%d_%H%M%S")
        file_name = f"{file_path}{name}"

        pygame.image.save(self.screen, f"{file_name}.png")

        with open(f"{file_name}.png", "rb") as f:
            base64_string = base64.b64encode(f.read())

        if save:
            target_dir = f"{file_path}{name}/"
            os.makedirs(target_dir)

            destPNG = os.path.join(target_dir, os.path.basename(f"{file_name}.png"))
            shutil.copy(f"{file_name}.png", destPNG)

            destTXT = os.path.join(target_dir, os.path.basename(f"{file_name}.txt"))
            with open(destTXT, "w") as f:
                f.write(base64_string.decode("utf-8"))

        os.remove(f"{file_name}.png")
        return base64_string

    def screen_Loop(self, objects):
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                self.running = False
            if event.type == pygame.KEYDOWN:
                self.clickCallback(event.key)

        self.screen.fill(self.color["background"])        
        
        for gamer in range(self.config["game"]["playerNum"]-2,-2,-1):      
            self.space[gamer].step(1/self.FPS)
            

            # ATUALIZAR POSIÇÕES

            for obj in objects[f"P{gamer+1}"][gamer == -1:]:
                obj.draw()



        pos_mouse_mainPlayer = pygame.mouse.get_pos()
        objects[f"P0"][0].body.position = pos_mouse_mainPlayer
        objects[f"P0"][0].draw()        

        pygame.display.flip()

        self.clock.tick(self.FPS)

    def close(self):
        pygame.quit()
        sys.exit()