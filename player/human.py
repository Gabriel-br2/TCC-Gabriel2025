import random
import pymunk
import pygame

class HumanPlayer:
    def __init__(self, screen, color, initial_position, size, space=None):
        self.initial_position = initial_position
        self.type = "HumanPlayer"
        self.screen = screen
        self.size = size
        self.color = color

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.initial_position[0], self.initial_position[1]

        self.shape = pymunk.Circle(self.body, size)
        self.shape.collision_type = 3
        self.shape.elasticity = 1
        self.shape.density = 1

        if space is not None:
            space.add(self.body, self.shape)

    def draw(self, color=None, position=None, angle=None):
        if position is None and color is None:
            position = self.body.position
            color = self.color
    
        x, y = position
        pygame.draw.circle(self.screen, color, (int(x), int(y)), self.size)