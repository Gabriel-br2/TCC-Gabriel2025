import pygame
import pymunk

class generic:
    def __init__(self, screen, space, color, tam = 20):
        self.InitPos = (400, 400)
        self.color = color
        self.tam = tam
        self.type = "genericSquare"
        self.screen = screen

        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = self.InitPos[0], self.InitPos[1]

        self.shape = pymunk.Poly.create_box(self.body, (tam, tam))

        self.shape.mass = 1
        self.shape.elasticity = 1

        space.add(self.body, self.shape)

    def draw(self):

        
        pygame.draw.rect(self.screen, self.color["red"], (self.body.position.x - self.tam//2, self.body.position.y - self.tam//2, self.tam, self.tam))  