import pygame
from LLM.local import *
from players.motion import *
from utils.colision import *


def LLMInteraction(_, my_objects):
    interpretation = obtain_image_description(path="screendata/last.jpg")
    command = get_command_movement(interpretation)

    obj = my_objects[command["object_id"]]

    if command["action"] == "move":
        return move_object(obj, command["dx"], command["dy"], my_objects)

    elif command["action"] == "rotate":
        rotate_object(obj)
        return True
