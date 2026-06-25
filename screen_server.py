import os
import threading
import webbrowser

import pygame


class ScreenMonitor:
    def __init__(self, config, color, models):
        pygame.init()

        self.config = config
        self.color = color

        self.fps = 60
        self.iou = 0.0
        self.lock = True
        self.game_running = True
        self.models = models

        self.width = config["screen"]["width"]
        self.height = config["screen"]["height"]

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18, bold=True)

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("server monitor")

    def game_loop(self, objects, iou):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_running = False
                self.close()

        self._render(objects, iou)
        self.clock.tick(self.fps)

    # --- Renderização ---
    def _render(self, objects, iou):
        self.screen.fill(self.color["background"])
        self._draw_objects(objects)
        self._draw_iou(iou)
        pygame.display.flip()

    def _draw_objects(self, objects):
        for player in objects.values():
            if type(player) is not dict:
                continue

            for obj in player["pos"]:
                transform_points = []

                model = self.models[obj[3]]
                for point in model:
                    x, y = point
                    obj[2] = obj[2] % 360

                    if obj[2] == 90:
                        x, y = -y, x
                    elif obj[2] == 180:
                        x, y = -x, -y
                    elif obj[2] == 270:
                        x, y = y, -x
                    x += obj[0]
                    y += obj[1]
                    transform_points.append((x, y))

                pygame.draw.polygon(
                    self.screen, self.color[player["color"]], transform_points
                )
                pygame.draw.polygon(self.screen, (0, 0, 0), transform_points, 2)

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
