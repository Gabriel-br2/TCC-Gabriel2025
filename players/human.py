import pygame

from utils.colision import *


def humanInteraction(event, objects, my_objects):

    if event.type == pygame.MOUSEBUTTONDOWN:
        for my_obj in reversed(my_objects):
            if point_in_polygon(event.pos, my_obj.transformed_vertices):
                if event.button == 3:
                    my_obj.rotate()

                if event.button == 1:
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

                new_x = event.pos[0] + my_obj.offset_x
                new_y = event.pos[1] + my_obj.offset_y

                temp_new_pos = my_obj.get_transformed_position(
                    [new_x, new_y], my_obj.position[-1]
                )

                collides = False
                for other_my_obj in my_objects:
                    if other_my_obj != my_obj:
                        temp_other_pos = other_my_obj.get_transformed_position(
                            other_my_obj.position[:-1], other_my_obj.position[-1]
                        )

                        if detect_polygon_intersection(temp_new_pos, temp_other_pos):
                            collides = True
                            break

                if not collides:
                    my_obj.position[0] = new_x
                    my_obj.position[1] = new_y
