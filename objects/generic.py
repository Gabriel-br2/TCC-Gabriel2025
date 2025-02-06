import pygame
import pymunk

class GenericShape:
    """
    Represents a generic, dynamic, rectangular shape in the simulation.

    This class manages the shape's physical properties (position, rotation, etc.) using Pymunk
    and handles drawing the shape on the screen using Pygame.
    """
    def __init__(self, screen, color, initial_position, size, space=None):
        """
        Initializes the GenericShape object.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
            color (tuple): The color of the shape (RGB tuple).
            initial_position (tuple): The initial (x, y) position of the shape's center.
            size (int): The side length of the square shape.
            space (pymunk.Space, optional): The Pymunk space to add the shape's body and shape to. Defaults to None.
        """
        self.type = "generic"  # Identifies the object type
        self.initial_position = initial_position 
        self.screen = screen
        self.color = color
        self.size = size 

        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)  # Dynamic body for physics simulation
        self.body.position = self.initial_position[0], self.initial_position[1]

        self.shape = pymunk.Poly.create_box(self.body, (size, size)) # create a box shape

        self.shape.elasticity = 1  # Elasticity of collisions
        self.shape.mass = 1  # Mass of the shape

        self.vertices = self.shape.get_vertices()  # Get the vertices of the shape

        if space is not None:
            space.add(self.body, self.shape)  # Add to the physics space

    def get_transformed_position(self, position, angle):
        """
        Gets the transformed vertices of the shape after rotation and translation.

        Args:
            position (pymunk.Vec2d): The position of the shape's center.
            angle (float): The rotation angle in radians.

        Returns:
            list: A list of tuples, where each tuple represents a transformed vertex (x, y).
        """
        transformed_vertices = [(vertex.rotated(angle) + position) for vertex in self.vertices]
        return [(int(x), int(y)) for x, y in transformed_vertices]  # Convert to integers for Pygame

    def draw(self, color=None, position=None, angle=None):
        """
        Draws the shape on the screen.

        Args:
            color (tuple, optional): The color to draw the shape. Defaults to the shape's color.
            position (pymunk.Vec2d, optional): The position to draw the shape. Defaults to the shape's current position.
            angle (float, optional): The rotation angle. Defaults to the shape's current angle.

        Returns:
            None
        """
        if angle is None and position is None and color is None:
            position = self.body.position
            angle = self.body.angle
            color = self.color

        pygame.draw.polygon(self.screen, color, self.get_transformed_position(position, angle)) # draws the polygon