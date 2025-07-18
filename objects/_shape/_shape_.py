import math
import time

import pygame


class Shape:
    def __init__(self, screen, color, initial_position, cfg, vertices, shape_type):
        self.type = shape_type
        self.screen = screen
        self.color = color
        self.position = initial_position
        self.winsize = (cfg.data["screen"]["width"], cfg.data["screen"]["height"])
        self.vertices = vertices

        self.isMoving = False
        self.isRotating = False
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0

        self.update_position()

    def rotate(self):
        self.isRotating = True

    def get_transformation_matrix(self, position, angle_deg):
        angle_rad = math.radians(angle_deg)
        c_theta = math.cos(angle_rad)
        s_theta = math.sin(angle_rad)
        tx, ty = position

        return [[c_theta, -s_theta, tx], [s_theta, c_theta, ty], [0, 0, 1]]

    def apply_transformation(self, vertex, matrix):
        x, y = vertex
        x_new = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]
        y_new = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]
        return (int(x_new), int(y_new))

    def get_transformed_position(self, position, angle):
        matrix = self.get_transformation_matrix(position, angle)
        return [self.apply_transformation(vertex, matrix) for vertex in self.vertices]

    def update_position(self):
        self.transformed_vertices = self.get_transformed_position(
            self.position[:-1], self.position[-1]
        )

    def draw(self):
        if self.isRotating:
            self.position[-1] += 10
            if self.position[-1] % 90 == 0:
                self.isRotating = False

        self.update_position()

        polygon_surface = pygame.Surface(self.winsize, pygame.SRCALPHA)
        pygame.draw.polygon(polygon_surface, self.color, self.transformed_vertices)
        pygame.draw.polygon(
            polygon_surface, (0, 0, 0, self.color[-1]), self.transformed_vertices, 1
        )

        self.screen.blit(polygon_surface, (0, 0))

    def interpolacao_linear(self, posicao_inicial, delta, p):
        x_inicial, y_inicial = posicao_inicial
        delta_x, delta_y = delta
        x_interpolado = x_inicial + (delta_x * p)
        y_interpolado = y_inicial + (delta_y * p)
        return (x_interpolado, y_interpolado, 0)

    def moveLinear(self, delta=None, incremento_p=None):
        if not self.isMoving:
            self.isMoving = True
            self.trajetoria = self.gerar_pontos_interpolados(
                self.position[:-1], delta, incremento_p
            )
        else:
            temp = self.trajetoria.pop(0)
            self.position[0] = temp[0]
            self.position[1] = temp[1]

            time.sleep(0.5)

            self.update_position()
            if len(self.trajetoria) == 0:
                self.isMoving = False

    def gerar_pontos_interpolados(self, posicao_inicial, delta, incremento_p):
        trajetoria = []
        p_atual = 0.0

        while p_atual <= 1.0:
            ponto = self.interpolacao_linear(posicao_inicial, delta, p_atual)
            trajetoria.append(ponto)
            p_atual += incremento_p

        if trajetoria[-1] != self.interpolacao_linear(posicao_inicial, delta, 1.0):
            ponto_final = self.interpolacao_linear(posicao_inicial, delta, 1.0)
            trajetoria.append(ponto_final)

        return trajetoria
