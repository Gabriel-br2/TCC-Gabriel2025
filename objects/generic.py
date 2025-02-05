import pygame
import pymunk

class GenericShape:
    def __init__(self, screen, color, initial_position, size, space=None):
        self.type = "generic"
        self.initial_position = initial_position 
        self.screen = screen
        self.color = color
        self.size = size 

        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = self.initial_position[0], self.initial_position[1]

        self.shape = pymunk.Poly.create_box(self.body, (size, size))

        self.shape.elasticity = 1
        self.shape.mass = 1

        self.vertices = self.shape.get_vertices()

        if space is not None:
            space.add(self.body, self.shape)

    def get_transformed_position(self, position, angle):
        transformed_vertices = [(vertex.rotated(angle) + position) for vertex in self.vertices]
        return [(int(x), int(y)) for x, y in transformed_vertices]

    def draw(self, color=None, position=None, angle=None):
        if angle is None and position is None and color is None:
            position = self.body.position
            angle = self.body.angle
            color = self.color

        pygame.draw.polygon(self.screen, color, self.get_transformed_position(position, angle))
