import pygame

from players.motion import *
from utils.colision import point_in_polygon


def humanInteraction(event, objects, my_objects, cfg):
    if event.type == pygame.MOUSEBUTTONDOWN:
        for my_obj in reversed(my_objects):
            if point_in_polygon(event.pos, my_obj.transformed_vertices):
                if event.button == 3:  # botão direito → rotaciona
                    rotate_object(my_obj)

                if event.button == 1:  # botão esquerdo → inicia drag
                    my_obj.dragging = True
                    my_obj.offset_x = my_obj.position[0] - event.pos[0]
                    my_obj.offset_y = my_obj.position[1] - event.pos[1]
                break

    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            for my_obj in my_objects:
                if my_obj.dragging:
                    my_obj.dragging = False

    elif event.type == pygame.MOUSEMOTION:
        for my_obj in my_objects:
            if my_obj.dragging:
                dx = (event.pos[0] + my_obj.offset_x) - my_obj.position[0]
                dy = (event.pos[1] + my_obj.offset_y) - my_obj.position[1]
                move_object(my_obj, dx, dy, my_objects, cfg)
