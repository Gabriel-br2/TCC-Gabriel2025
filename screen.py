import os

import pygame
from players.human import humanInteraction
from players.LLM import LLMInteraction


class Screen:
    def __init__(self, config, color, client_id, player_type):
        pygame.init()

        self.config = config
        self.color = color
        self.client_id = client_id
        self.player_type = player_type

        self.fps = 60
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
        local_player_objects = objects[-self.config["game"]["objectsNum"] :]

        self._handle_events(objects, local_player_objects)
        self._render(objects, iou)

        self.clock.tick(self.fps)

        # Retorna posições do jogador local
        return [[*obj.position, obj.type] for obj in local_player_objects]

    # --- Input ---
    def _handle_events(self, objects, local_objects):
        if self.player_type == "human":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                    return
                humanInteraction(event, objects, local_objects)

        if self.player_type == "LLM":
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
            LLMInteraction(objects, local_objects)

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
