import math
import pygame
import pymunk

class LLMPlayer:
    def __init__(self, space, color, size=25):
        self.initial_position = (100, 100)
        self.type = "player"
        
        self.size = size
        self.color = color

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.initial_position
        
        self.shape = pymunk.Circle(self.body, size)
        self.shape.collision_type = 3
        self.shape.elasticity = 1
        self.shape.density = 1

        space.add(self.body, self.shape)

        self.moving_path = []
        self.is_moving = False

    def update_position(self, interpolation=1):
        if self.moving_path:
            self.body.position = self.moving_path.pop(0)
        else:
            actual_x, actual_y = self.body.position
            x_move, y_move = map(int, input().split())

            goal_x, goal_y = actual_x + x_move, actual_y + y_move
            total_distance = math.sqrt((goal_x - actual_x) ** 2 + (goal_y - actual_y) ** 2)
            num_segments = max(1, int(total_distance // interpolation))

            for i in range(num_segments + 1):
                t = i / num_segments
                x = actual_x + t * (goal_x - actual_x)
                y = actual_y + t * (goal_y - actual_y)
                self.moving_path.append((x, y))