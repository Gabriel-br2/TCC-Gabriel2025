import math

import pygame


class LoadingSpinner:
    """Animated circular loading indicator drawn with a rotating arc."""

    def __init__(
        self,
        center: tuple[int, int],
        radius: int = 32,
        color: tuple[int, int, int] = (0, 0, 0),
        thickness: int = 5,
        arc_span: float = math.pi * 1.35,
        speed: float = 0.006,
    ):
        self.center = center
        self.radius = radius
        self.color = color
        self.thickness = thickness
        self.arc_span = arc_span
        self.speed = speed

    def draw(self, surface: pygame.Surface) -> None:
        angle = pygame.time.get_ticks() * self.speed
        rect = pygame.Rect(
            self.center[0] - self.radius,
            self.center[1] - self.radius,
            self.radius * 2,
            self.radius * 2,
        )
        pygame.draw.arc(
            surface,
            self.color,
            rect,
            angle,
            angle + self.arc_span,
            self.thickness,
        )
