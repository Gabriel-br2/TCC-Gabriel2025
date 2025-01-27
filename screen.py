import pygame
import pymunk
import pymunk.pygame_util

import os
import sys
import shutil
import base64
import datetime

class screen:
    def __init__(self, config, color, clickCallback, ClientId, Color, debug=False):
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
        self.space = pymunk.Space()

        self.space.gravity = (0, 0)
        self.FPS = 60

        self.font = pygame.font.SysFont("Arial", 18, bold=True)

        self.screen = pygame.display.set_mode((self.screen_Width, self.screen_Height))
        pygame.display.set_caption(config['screen']['caption'] + f" - player: {ClientId} - {Color}")

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

    def screen_LoopGame(self, setNewPosition, getNewPosition, client_socket, objects, id, iou):
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                self.GameRunning = False
            if event.type == pygame.KEYDOWN:
                self.clickCallback(event.key)

        self.screen.fill(self.color["background"])        
        self.space.step(1/self.FPS)            
        
        # Desenhar objetos que não são do cliente principal
        for gamer in range(self.config["game"]["playerNum"]):      
            if id != gamer:
                for obj in objects["you"][f"P{gamer}"]["pos"]:
                    objects[obj[3]].draw(self.color[objects["you"][f"P{gamer}"]["color"]], obj[:2], obj[2])
                    
        update = []
        pos_mouse_mainPlayer = pygame.mouse.get_pos()
        objects[f"me"][0].body.position = pos_mouse_mainPlayer
        objects[f"me"][0].draw()   

        for obj in objects[f"me"]:
            x, y = obj.body.position

            update.append([x,y,obj.body.angle, obj.type])
            obj.draw()

        new_position = update
        setNewPosition(client_socket, new_position)

        data = getNewPosition(client_socket)
        
        for gamer in range(self.config["game"]["playerNum"]):      
            if id != gamer:
                for obj in range(len(objects["you"][f"P{gamer}"]["pos"])):
                    objects["you"][f"P{gamer}"]["pos"][obj] = data[f"P{gamer}"]["pos"][obj]

        iou = data["IoU"]        
        texto = self.font.render(f"Objetivo Concluido: {float(iou)*100:.2f} %", True, (0,0,0))
        texto_rect = texto.get_rect(center=(self.config["screen"]["width"] // 2, 25))
        self.screen.blit(texto, texto_rect)

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