import pygame
import pymunk
import pymunk.pygame_util
import os
import sys
import shutil
import base64
import datetime

class Screen:
    def __init__(self, config, color, click_callback, client_id, player_color, debug=False):
        pygame.init()

        self.menu_running = True
        self.game_running = True
        self.debug = debug
        self.color = color
        self.config = config
        self.click_callback = click_callback

        self.screen_height = config['screen']['height']
        self.screen_width = config['screen']['width']

        self.clock = pygame.time.Clock()
        self.space = pymunk.Space()

        self.space.gravity = (0, 0)
        self.fps = 60

        self.font = pygame.font.SysFont("Arial", 18, bold=True)

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(f"{config['screen']['caption']} - player: {client_id} - {player_color}")

    def screenshot_base64(self, save=False, file_path='screenshot/'):
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        file_name = f"{file_path}{timestamp}"

        pygame.image.save(self.screen, f"{file_name}.png")

        with open(f"{file_name}.png", "rb") as f:
            base64_string = base64.b64encode(f.read())

        if save:
            target_dir = f"{file_path}{timestamp}/"
            os.makedirs(target_dir)

            dest_png = os.path.join(target_dir, os.path.basename(f"{file_name}.png"))
            shutil.copy(f"{file_name}.png", dest_png)

            dest_txt = os.path.join(target_dir, os.path.basename(f"{file_name}.txt"))
            with open(dest_txt, "w") as f:
                f.write(base64_string.decode("utf-8"))

        os.remove(f"{file_name}.png")
        return base64_string

    def game_loop(self, set_new_position, get_new_position, client_socket, objects, player_id, iou):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_running = False
            if event.type == pygame.KEYDOWN:
                self.click_callback(event.key)

        self.screen.fill(self.color["background"])
        self.space.step(1 / self.fps)

        for player_index in range(self.config["game"]["playerNum"]):
            if player_id != player_index:
                for obj in objects["you"][f"P{player_index}"]["pos"]:
                    objects[obj[3]].draw(self.color[objects["you"][f"P{player_index}"]["color"]], obj[:2], obj[2])

        mouse_pos = pygame.mouse.get_pos()
        objects["me"][0].body.position = mouse_pos
        objects["me"][0].draw()

        updated_positions = []
        for obj in objects["me"]:
            x, y = obj.body.position
            updated_positions.append([x, y, obj.body.angle, obj.type])
            obj.draw()

        new_position = updated_positions
        set_new_position(client_socket, new_position)

        data = get_new_position(client_socket)
        for player_index in range(self.config["game"]["playerNum"]):
            if player_id != player_index:
                objects["you"][f"P{player_index}"]["pos"] = data[f"P{player_index}"]["pos"]

        iou = data["IoU"]
        iou_text = self.font.render(f"Objetivo Concluído: {iou * 100:.2f} %", True, (0, 0, 0))
        text_rect = iou_text.get_rect(center=(self.config["screen"]["width"] // 2, 25))
        self.screen.blit(iou_text, text_rect)

        pygame.display.flip()
        self.clock.tick(self.fps)

    def close(self):
        pygame.quit()
        sys.exit()
