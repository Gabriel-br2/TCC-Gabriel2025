import pygame
import pymunk

class human_Player:
    def __init__(self, screen, space, color, tam = 10):
        self.InitPos = (250, 250)
        self.color = color
        self.tam = tam
        self.type = "human"
        self.screen = screen

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.InitPos[0], self.InitPos[1]

        self.shape = pymunk.Circle(self.body, tam)

        self.shape.elasticity = 1
        self.shape.density = 1

        self.shape.collision_type = 3

        space.add(self.body, self.shape)

    def draw(self):
        pygame.draw.circle(self.screen, self.color["blue"], (int(self.body.position.x), int(self.body.position.y)), self.tam)