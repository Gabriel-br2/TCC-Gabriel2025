import random

import pygame
import pymunk


class HumanPlayer:
    """
    Represents a human player in the simulation.

    This class manages the player's physical representation (circle), position, and drawing on the screen.
    It uses PyMunk for physics and Pygame for rendering.
    """

    def __init__(self, screen, color, initial_position, cfg, space=None):
        """
        Initializes the HumanPlayer object.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
            color (tuple): The color of the player (RGB tuple).
            initial_position (tuple): The initial (x, y) position of the player.
            size (int): The radius of the player's circle.
            space (pymunk.Space, optional): The PyMunk space to add the player's body and shape to. Defaults to None.
        """
        self.initial_position = initial_position
        self.type = "HumanPlayer"  # Identifies the object type
        self.screen = screen
        self.winsize = (cfg.data["screen"]["height"], cfg.data["screen"]["width"])
        self.size = cfg.data["game"]["playerTam"]
        self.color = color

        self.body = pymunk.Body(
            body_type=pymunk.Body.KINEMATIC
        )  # Kinematic body for player control
        self.body.position = self.initial_position[0], self.initial_position[1]

        self.shape = pymunk.Circle(self.body, self.size)  # Circular shape for collision
        self.shape.collision_type = 3  # Collision type identifier
        self.shape.elasticity = 1  # Elasticity of collisions
        self.shape.density = 1  # density of the player's shape

        if space is not None:
            space.add(self.body, self.shape)  # Add to the physics space

    def draw(self, color=None, position=None, angle=None):
        """
        Draws the player on the screen.

        Args:
            color (tuple, optional): The color to draw the player. Defaults to the player's color.
            position (tuple, optional): The position to draw the player. Defaults to the player's current position.
            angle (float, optional): The drawing angle. Currently unused.

        Returns:
            None
        """
        if position is None and color is None:
            position = self.body.position
            color = self.color

        x, y = position
        polygon_surface = pygame.Surface(self.winsize, pygame.SRCALPHA)
        pygame.draw.circle(polygon_surface, color, (int(x), int(y)), self.size)
        self.screen.blit(polygon_surface, (0, 0))
