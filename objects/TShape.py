import pygame
import pymunk

class TeeweeShape:
    def __init__(self, screen, color, initial_position, size, space=None):
        self.type = "teewee"
        self.initial_position = initial_position  
        self.screen = screen 
        self.color = color  
        self.size = size / 1.25  

        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = self.initial_position[0], self.initial_position[1]

        self.vertices1 = [
            (-self.size * 1.5, 0),
            (-self.size * 1.5, self.size),
            (self.size * 1.5, self.size),
            (self.size * 1.5, 0)
        ]

        self.vertices2 = [
            (-self.size * 0.5, self.size),
            (-self.size * 0.5, self.size * 2),
            (self.size * 0.5, self.size * 2), 
            (self.size * 0.5, self.size)          
        ]

        self.shape1 = pymunk.Poly(self.body, self.vertices1)
        self.shape2 = pymunk.Poly(self.body, self.vertices2)

        self.shape1.elasticity = 1
        self.shape2.elasticity = 1

        self.shape1.mass = 1
        self.shape2.mass = 1

        self.vertices = self.shape1.get_vertices()[:-1] + self.shape2.get_vertices()[1:] + [self.shape2.get_vertices()[0]] + [self.shape1.get_vertices()[-1]]

        if space is not None:
            space.add(self.body, self.shape1, self.shape2)

    def get_transformed_position(self, position, angle):
        transformed_vertices = [(vertex.rotated(angle) + position) for vertex in self.vertices]
        return [(int(x), int(y)) for x, y in transformed_vertices]

    def draw(self, color=None, position=None, angle=None):
        if angle is None and position is None and color is None:
            position = self.body.position
            angle = self.body.angle
            color = self.color

        transformed_vertices = self.get_transformed_position(position, angle)
        pygame.draw.polygon(self.screen, color, transformed_vertices)
