import pygame
import pymunk


class TeeweeShape:
    """
    Represents a "Teewee" shaped object in the simulation.  This shape is composed of two rectangles.

    This class manages the shape's physical properties (position, rotation, etc.) using Pymunk
    and handles drawing the shape on the screen using Pygame.
    """

    def __init__(self, screen, color, initial_position, cfg, space=None):
        """
        Initializes the TeeweeShape object.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
            color (tuple): The color of the shape (RGB tuple).
            initial_position (tuple): The initial (x, y) position of the shape's center.
            size (int): A scaling factor for the size of the shape.
            space (pymunk.Space, optional): The Pymunk space to add the shape's body and shapes to. Defaults to None.
        """
        self.type = "teewee"  # Identifies the object type
        self.initial_position = initial_position
        self.screen = screen
        self.color = color
        self.winsize = (cfg.data["screen"]["height"], cfg.data["screen"]["width"])
        self.size = (
            cfg.data["game"]["objectBaseSquareTam"] / 1.25
        )  # Adjust size for visual consistency

        self.body = pymunk.Body(
            body_type=pymunk.Body.DYNAMIC
        )  # Dynamic body for physics simulation
        self.body.position = self.initial_position[0], self.initial_position[1]

        # Define vertices for the two rectangular parts of the "T" shape.
        self.vertices1 = [
            (-self.size * 1.5, 0),
            (-self.size * 1.5, self.size),
            (self.size * 1.5, self.size),
            (self.size * 1.5, 0),
        ]

        self.vertices2 = [
            (-self.size * 0.5, self.size),
            (-self.size * 0.5, self.size * 2),
            (self.size * 0.5, self.size * 2),
            (self.size * 0.5, self.size),
        ]

        self.shape1 = pymunk.Poly(
            self.body, self.vertices1
        )  # Create the first rectangle shape
        self.shape2 = pymunk.Poly(
            self.body, self.vertices2
        )  # Create the second rectangle shape

        self.shape1.elasticity = 1  # Elasticity of collisions
        self.shape2.elasticity = 1  # Elasticity of collisions

        self.shape1.mass = 1  # Mass of the shape
        self.shape2.mass = 1  # Mass of the shape

        # Combine vertices for drawing the whole shape
        self.vertices = (
            self.shape1.get_vertices()[:-1]
            + self.shape2.get_vertices()[1:]
            + [self.shape2.get_vertices()[0]]
            + [self.shape1.get_vertices()[-1]]
        )

        if space is not None:
            space.add(self.body, self.shape1, self.shape2)  # Add to the physics space

    def get_transformed_position(self, position, angle):
        """
        Gets the transformed vertices of the shape after rotation and translation.

        Args:
            position (pymunk.Vec2d): The position of the shape's center.
            angle (float): The rotation angle in radians.

        Returns:
            list: A list of tuples, where each tuple represents a transformed vertex (x, y).
        """
        transformed_vertices = [
            (vertex.rotated(angle) + position) for vertex in self.vertices
        ]
        return [
            (int(x), int(y)) for x, y in transformed_vertices
        ]  # Convert to integers for Pygame

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

        polygon_surface = pygame.Surface(self.winsize, pygame.SRCALPHA)
        transformed_vertices = self.get_transformed_position(position, angle)
        pygame.draw.polygon(
            polygon_surface, color, transformed_vertices
        )  # Draw the combined polygon
        self.screen.blit(polygon_surface, (0, 0))
