import random
import pymunk
import pygame

class human_Player:
    def __init__(self, screen, space, color, tam = 10):
        self.InitPos = (random.randint(0,500), random.randint(0,500))
        self.type = "human"
        self.screen = screen

        self.tam = tam
        self.color = color

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.InitPos[0], self.InitPos[1]

        self.shape = pymunk.Circle(self.body, tam)
        self.shape.collision_type = 3
        self.shape.elasticity = 1
        self.shape.density = 1

        space.add(self.body, self.shape)

    def draw(self):
        x, y = self.body.position
        pygame.draw.circle(self.screen, self.color, (int(x), int(y)), self.tam)
