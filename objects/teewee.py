import pygame
import pymunk

class teewee:
    def __init__(self, screen, color, InitPos, tam, space=None):
        self.type = "teewee"
        self.InitPos = InitPos
        self.screen = screen
        self.color = color
        tam = tam/1.25

        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = self.InitPos[0], self.InitPos[1]

        vertices1 = [
            (-tam * 1.5, 0),
            (-tam * 1.5, tam),
            ( tam * 1.5, tam),
            ( tam * 1.5, 0)
        ]

        vertices2 = [
            (-tam * 0.5, tam),
            (-tam * 0.5, tam * 2),
            (tam * 0.5, tam * 2), 
            (tam * 0.5, tam)          
        ]

        self.shape1 = pymunk.Poly(self.body, vertices1)
        self.shape2 = pymunk.Poly(self.body, vertices2)

        self.shape1.elasticity = 1
        self.shape2.elasticity = 1

        self.shape1.mass = 1
        self.shape2.mass = 1

        v1 = self.shape1.get_vertices()
        v2 = self.shape2.get_vertices()

        self.vertices = v1[:-1] + v2[1:] + [v2[0]] + [v1[-1]]

        if space is not None:
           space.add(self.body, self.shape1, self.shape2)

    def getPosition(self, position, angle):
        transformed_vertices = [(v.rotated(angle) + position) for v in self.vertices]
        return [(int(x), int(y)) for x, y in transformed_vertices]

    def draw(self, color=None, position=None, angle=None):

        if angle is None and position is None and color is None:
                position = self.body.position
                angle = self.body.angle
                color = self.color

        v = self.getPosition(position, angle)

        # Desenhar os vértices
        # for vertex in v:
        #     pygame.draw.circle(self.screen, (255,0,0), vertex, 5)  # Desenha um círculo pequeno em cada vértice

        pygame.draw.polygon(self.screen, color, v)