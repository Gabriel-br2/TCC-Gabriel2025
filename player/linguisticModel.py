import math
import pygame
import pymunk

class LLM_Player:
    def __init__(self, space, color, tam=25):
        self.InitPos = (100, 100)
        self.type = "LLM"
        
        self.tam = tam
        self.color = color

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.InitPos[0], self.InitPos[1]
        
        self.shape = pymunk.Circle(self.body, tam)
        self.shape.collision_type = 3
        self.shape.elasticity = 1
        self.shape.density = 1

        space.add(self.body, self.shape)

        self.movingPath = []
        self.isMoving = False

    def setPosition(self, iterpolation=1):
        if len(self.movingPath) > 0:
            self.body.position = self.movingPath[0]
            self.movingPath.pop(0) 

        else:
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