from utils.colision import detect_polygon_intersection


def move_object(my_obj, dx, dy, my_objects):
    new_x = my_obj.position[0] + dx
    new_y = my_obj.position[1] + dy

    temp_new_pos = my_obj.get_transformed_position([new_x, new_y], my_obj.position[-1])

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
        return True

    return False


def rotate_object(my_obj):
    my_obj.rotate()
