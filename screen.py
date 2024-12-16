import pygame
import pymunk
import pymunk.pygame_util

import os
import sys
import json
import shutil
import base64
import datetime

class screen:
    def __init__(self, config, color, clickCallback, debug=False):
        pygame.init()

        self.MenuRunning   = True
        self.GameRunning   = True
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

    def screen_LoopGame(self, setNewPosition, getNewPosition, client_socket, objects, id):
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                self.GameRunning = False
            if event.type == pygame.KEYDOWN:
                self.clickCallback(event.key)

        self.screen.fill(self.color["background"])        
        
        for gamer in range(self.config["game"]["playerNum"]):      
            self.space[gamer].step(1/self.FPS)            

            if id != gamer:
                for obj in objects[f"P{gamer}"][0:]:
                    obj.draw()

        update = []
        pos_mouse_mainPlayer = pygame.mouse.get_pos()
        objects[f"P{id}"][0].body.position = pos_mouse_mainPlayer
        objects[f"P{id}"][0].draw()   

        update.append(pos_mouse_mainPlayer)

        for obj in objects[f"P{id}"][1:]:
            update.append(obj.body.position)
            obj.draw()

        new_position = update
        setNewPosition(client_socket, new_position)

        data = getNewPosition(client_socket)
        
        for gamer in range(self.config["game"]["playerNum"]):      
            if id != gamer:
                for obj in range(len(objects[f"P{gamer}"])-1):
                    objects[f"P{gamer}"][obj].body.position = data[f"P{gamer}"]["pos"][obj]

        pygame.display.flip()

        self.clock.tick(self.FPS)

    def screen_MenuLoop(self):
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                self.MenuRunning = False
            if event.type == pygame.KEYDOWN:
                self.clickCallback(event.key)

        self.screen.fill(self.color["background"])   


        




        pygame.display.flip()

        self.clock.tick(self.FPS)



    def close(self):
        pygame.quit()
        sys.exit()