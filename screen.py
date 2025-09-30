import os
import threading
import webbrowser

import pygame
from dotenv import load_dotenv
from players.human import humanInteraction
from players.LLM import LLM_PLAYER

load_dotenv()
URL = os.getenv("FORM_URL")


class Screen:
    def __init__(
        self, config, color, client_id, timestamp, player_type, LLM_source="local"
    ):
        pygame.init()

        self.config = config
        self.color = color
        self.client_id = client_id
        self.player_type = player_type

        if player_type == "LLM":
            self.LLM = LLM_PLAYER(timestamp, client_id, LLM_source)

        self.fps = 60
        self.iou = 0.0
        self.lock = True
        self.menu_running = True
        self.game_running = True

        self.width = config["screen"]["width"]
        self.height = config["screen"]["height"]

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18, bold=True)

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(
            f"{config['screen']['caption']} - player: {client_id}"
        )

    # --- Loop principal ---
    def game_loop(self, objects, iou):
        local_player_objects = [obj for obj in objects if obj.id == self.client_id]

        self._render(objects, iou)
        self._handle_events(objects, local_player_objects)

        self.clock.tick(self.fps)

        return [[*obj.position, obj.type] for obj in local_player_objects]

    def change_screen(self):
        large_font = pygame.font.SysFont("Arial", self.width // 35, bold=True)
        text_surface = large_font.render(
            "Objetivo concluído, iniciando próximo ciclo", True, (0, 0, 0)
        )
        text_rect = text_surface.get_rect(center=(self.width / 2, self.height / 2))
        self.screen.fill(self.color["background"])

        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()
        pygame.time.wait(3000)

    def end_screen(self):
        end_font = pygame.font.SysFont("Arial", self.width // 35, bold=True)
        end_text = end_font.render(
            "Experimento concluído! Por favor responda o Questinário:", True, (0, 0, 0)
        )
        end_rect = end_text.get_rect(center=(self.width / 2, self.height / 2))

        end_font.set_underline(True)
        link_text = end_font.render("Questionário via Google Forms", True, (0, 0, 255))
        link_rect = link_text.get_rect(center=(self.width / 2, self.height / 2 + 150))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if link_rect.collidepoint(event.pos):
                        webbrowser.open(URL)

            self.screen.fill(self.color["background"])
            self.screen.blit(end_text, end_rect)
            self.screen.blit(link_text, link_rect)

            pygame.display.flip()
            self.clock.tick(self.fps)

    # --- Input ---
    def _handle_events(self, objects, local_objects):
        def human_events():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                    return
                humanInteraction(event, objects, local_objects)

        def LLM_events():
            if not os.path.exists("screendata"):
                os.makedirs("screendata")

            for obj in local_objects + objects:
                obj.draw_label(obj.id)
            pygame.image.save(self.screen, "screendata/last.jpg")
            for obj in local_objects + objects:
                obj.clear_label()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                    return
            self.LLM.LLMInteraction(objects, local_objects, self.iou)
            self.lock = True

        if self.player_type == "human":
            human_events()

        if self.player_type == "LLM":
            if self.lock:
                self.lock = False
                thread1 = threading.Thread(target=LLM_events)
                thread1.start()

    # --- Renderização ---
    def _render(self, objects, iou):
        self.screen.fill(self.color["background"])
        self._draw_objects(objects)
        self._draw_iou(iou)
        pygame.display.flip()

    def _draw_objects(self, objects):
        for obj in objects:
            obj.draw()

    def _draw_iou(self, iou):
        self.iou = iou
        text = self.font.render(
            f"Objetivo Concluído: {iou * 100:.2f} %", True, (0, 0, 0)
        )
        rect = text.get_rect(center=(self.width // 2, 25))
        self.screen.blit(text, rect)

    # --- Encerramento ---
    def close(self):
        pygame.quit()
