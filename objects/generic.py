import pygame
import pymunk

class generic:
    def __init__(self, screen, space, color, tam=20, InitPos=(400,400)):
        self.type = "genericSquare"
        self.InitPos = InitPos
        self.screen = screen
        self.color = color
        self.tam = tam

        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = self.InitPos[0], self.InitPos[1]

        self.shape = pymunk.Poly.create_box(self.body, (tam, tam))

        self.shape.elasticity = 1
        self.shape.mass = 1

        space.add(self.body, self.shape)
    
    def getPosition(self, shape_recev=None):
        vertices = self.shape.get_vertices()

        transformed_vertices = [(v.rotated(self.body.angle) + self.body.position) for v in vertices]
        return [(int(x), int(y)) for x, y in transformed_vertices]

    def draw(self):
        pygame.draw.polygon(self.screen, self.color, self.getPosition())