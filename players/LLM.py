import pygame
from utils.colision import *


def LLMInteraction(command, my_objects):
    print(command)

    if command["action"] == "rotate":
        for my_obj in my_objects:
            if my_obj.obj_id == int(command["obj_moved_id"]):
                a = int(command["pos"]) // 90
                for _ in range(a):
                    my_obj.rotate()
                break

    elif command["action"] == "move":
        for my_obj in my_objects:
            if my_obj.obj_id == int(command["obj_moved_id"]):
                posicao_final = [0, 0]
                try:
                    pos_str = command["pos"].strip()
                    pos_str_unificada = pos_str.replace(",", ";")
                    posicao_final = list(map(int, pos_str_unificada.split(";")))

                except (ValueError, KeyError, AttributeError) as e:
                    print(f"Erro ao processar o comando. Causa: {e}")

                my_obj.moveLinear(posicao_final, 0.3)

                break
