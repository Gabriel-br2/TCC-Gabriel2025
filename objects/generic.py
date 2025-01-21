import pygame
import pymunk

class generic:
    def __init__(self, screen, color, InitPos, tam, space=None):
        self.type = "generic"
        self.InitPos = InitPos
        self.screen = screen
        self.color = color
        self.tam = tam

        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = self.InitPos[0], self.InitPos[1]

        self.shape = pymunk.Poly.create_box(self.body, (tam, tam))

        self.shape.elasticity = 1
        self.shape.mass = 1

        if space is not None:
           space.add(self.body, self.shape)
    
    def getPosition(self, position, angle):
        vertices = self.shape.get_vertices()

        #print("v", type(vertices[0]), "|", vertices)
        #print("a", type(self.body.angle), self.body.angle)
        #print("p", type(self.body.position), self.body.position)

        transformed_vertices = [(v.rotated(angle) + position) for v in vertices]
        
        return [(int(x), int(y)) for x, y in transformed_vertices]

    def draw(self, position=None, angle=None):

        if angle is None and position is None:
                position = self.body.position
                angle = self.body.angle

        pygame.draw.polygon(self.screen, self.color, self.getPosition(position, angle))