import math
import pygame
import pymunk

class LLM_Player:
    def __init__(self, screen, color, initial_position, size, space=None):
        self.initial_position = initial_position
        self.type = "llmPlayer" 
        self.screen = screen
        self.size = size
        self.color = color

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.initial_position[0], self.initial_position[1]

        self.shape = pymunk.Circle(self.body, size)
        self.shape.collision_type = 3 
        self.shape.elasticity = 1
        self.shape.density = 1

        if space is not None:
            space.add(self.body, self.shape)

        self.movingPath = []
        self.isMoving = False

    def draw(self, color=None, position=None, angle=None):
        if position is None and color is None:
            position = self.body.position
            color = self.color
    
        x, y = position
        pygame.draw.circle(self.screen, color, (int(x), int(y)), self.size)

    def setPosition(self, iterpolation=1):
        if len(self.movingPath) == 0:
            actualPosX, actualPosY = self.body.position
            X_move, y_move = list(map(int,input().split(" ")))

            goal_posX, goal_posY = actualPosX + X_move, actualPosY + y_move

            distancia_total = math.sqrt((goal_posX - actualPosX)**2 + (goal_posY - actualPosY)**2)
            num_segmentos = max(1, int(distancia_total // iterpolation))

            for i in range(num_segmentos + 1):
                t = i / num_segmentos
                x = actualPosX + t * (goal_posX - actualPosX)
                y = actualPosY + t * (goal_posY - actualPosY)
                self.movingPath.append((x, y))
        
        r = self.movingPath[0]
        self.movingPath.pop(0) 
        return r