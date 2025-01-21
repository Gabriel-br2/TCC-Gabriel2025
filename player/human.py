import random
import pymunk
import pygame

class human_Player:
    def __init__(self, screen, color, InitPos, tam, space=None):
        self.InitPos = InitPos
        self.type = "player"
        self.screen = screen

        self.tam = tam
        self.color = color

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.InitPos[0], self.InitPos[1]

        self.shape = pymunk.Circle(self.body, tam)
        self.shape.collision_type = 3
        self.shape.elasticity = 1
        self.shape.density = 1

        if space is not None:
            space.add(self.body, self.shape)

    def draw(self, position=None):
        if position is None:
            position = self.body.position
    
        x, y = position
        pygame.draw.circle(self.screen, self.color, (int(x), int(y)), self.tam)
