import os
import threading

import pygame
from players.human import humanInteraction
from players.LLM import LLM_PLAYER


class Screen:
    def __init__(self, config, color, client_id, player_type, LLM_source="local"):
        pygame.init()

        self.config = config
        self.color = color
        self.client_id = client_id
        self.player_type = player_type

        if player_type == "LLM":
            self.LLM = LLM_PLAYER(LLM_source)

        self.fps = 60
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
        # <<< MUDANÇA: Seleciona os objetos do jogador local pelo ID, não pela posição na lista.
        local_player_objects = [obj for obj in objects if obj.id == self.client_id]

        self._render(objects, iou)
        self._handle_events(objects, local_player_objects)

        self.clock.tick(self.fps)

        # Retorna posições do jogador local
        return [[*obj.position, obj.type] for obj in local_player_objects]

    def change_screen(self):
        # self.width x self.height

        a = self.width // 20

        large_font = pygame.font.SysFont("Arial", a, bold=True)
        text_surface = large_font.render(
            "Objetivo concluído, iniciando próximo ciclo", True, (0, 0, 0)  # Cor preta
        )

        text_rect = text_surface.get_rect(center=(self.width / 2, self.height / 2))
        self.screen.fill(self.color["background"])

        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()
        pygame.time.wait(3000)

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
            self.LLM.LLMInteraction(objects, local_objects)
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
        text = self.font.render(
            f"Objetivo Concluído: {iou * 100:.2f} %", True, (0, 0, 0)
        )
        rect = text.get_rect(center=(self.width // 2, 25))
        self.screen.blit(text, rect)

    # --- Encerramento ---
    def close(self):
        pygame.quit()
