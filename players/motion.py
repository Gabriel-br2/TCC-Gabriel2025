import numpy as np

from utils.colision import detect_polygon_intersection


def dist(x, y):
    return (abs(x) ** 2 + abs(y) ** 2) ** 0.5


def get_interpolation(dx, dy):
    steps = int(max(abs(dx), abs(dy)))

    if steps == 0:
        return np.array([]), np.array([]), 0

    dx_l = np.linspace(0, dx, num=steps + 1)
    dy_l = np.linspace(0, dy, num=steps + 1)

    dx_l = np.round(dx_l).astype(int)
    dy_l = np.round(dy_l).astype(int)

    return dx_l[1:], dy_l[1:], steps


def move_object(my_obj, dx, dy, my_objects, cfg, LLM=False):
    start_x = my_obj.position[0]
    start_y = my_obj.position[1]

    if LLM:
        dx = dx - start_x
        dy = dy - start_y

    int_dx, int_dy, values = get_interpolation(dx, dy)

    if values == 0:
        return True

    okay = True
    for i in range(values):
        new_x = start_x + int_dx[i]
        new_y = start_y + int_dy[i]

        temp_new_pos = my_obj.get_transformed_position(
            [new_x, new_y], my_obj.position[-1]
        )
        for vertex_x, vertex_y in temp_new_pos:
            if (
                vertex_x < 0
                or vertex_x > cfg["screen"]["width"]
                or vertex_y < 0
                or vertex_y > cfg["screen"]["height"]
            ):
                okay = False
                break

        if not okay:
            break

        for other_my_obj in my_objects:
            if other_my_obj != my_obj:
                temp_other_pos = other_my_obj.get_transformed_position(
                    other_my_obj.position[:-1], other_my_obj.position[-1]
                )
                if detect_polygon_intersection(temp_new_pos, temp_other_pos):
                    okay = False
                    break

        if not okay:
            break

        my_obj.position[0] = int(new_x)
        my_obj.position[1] = int(new_y)

    return okay


def rotate_object(my_obj):
    my_obj.rotate()
