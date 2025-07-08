import json

import pygame
from players.human import humanInteraction
from players.LLM import LLMInteraction


class Screen:
    def __init__(self, config, color, client_id, api=None):
        pygame.init()

        self.fps = 60
        self.menu_running = True
        self.game_running = True

        self.color = color
        self.config = config
        self.client_id = client_id
        self.api = api

        self.turn = 0
        self.memory = [
            {
                "turn": self.turn,
                "action": "action",
                "obj_moved": "obj_moved",
                "pos": "",
                "thoughts": "start game",
            }
        ]

        self.screen_height = config["screen"]["height"]
        self.screen_width = config["screen"]["width"]

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18, bold=True)

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

        pygame.display.set_caption(
            f"{config['screen']['caption']} - player: {client_id}"
        )

    def generate_JSON(
        self, objects, iou, action=None, obj_moved=None, num=None, thoughts=None
    ):
        objects_json = {}
        for obj in objects:
            if obj.type not in objects_json:
                objects_json[obj.type] = obj.vertices

        agents_json = {}
        for obj in objects:
            if obj.id not in agents_json:
                agents_json[obj.id] = []

            agents_json[obj.id].append(
                {"id": obj.obj_id, "pos": [*obj.position, obj.type]}
            )

        self.memory.append(
            {
                "turn": self.turn,
                "action": action,
                "obj_moved": obj_moved,
                "pos" if type(num) == list else "pos": num,
                "thoughts": thoughts,
            }
        )

        data = {
            "turn": self.turn,
            "i_am": self.client_id,
            "vertices_model": objects_json,
            "agents": agents_json,
            "objective": iou * 100,
            "actions_options": ["move", "rotate"],
            "memory": self.memory,
        }

        self.turn += 1

        return data

    def game_loop(self, objects, iou):
        my_objects = objects[-self.config["game"]["objectsNum"] :]

        is_moving = False
        for obj in my_objects:
            if obj.isMoving or obj.isRotating:
                is_moving = True
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_running = False
                break

            if self.api is None:
                humanInteraction(event, objects, my_objects)

        if self.api is not None and not is_moving:

            if self.turn == 0:
                self.data = self.generate_JSON(objects, iou)

            self.api.generate(self.data)
            api_response = self.api.request()
            api_response = api_response.replace("```json", "").replace("```", "")

            try:
                api_response = json.loads(api_response)
            except:
                print("Error: ", api_response)
                self.memory.append(
                    {
                        "turn": self.turn,
                        "action": "action",
                        "obj_moved": "obj_moved",
                        "pos": "",
                        "thoughts": "error wrong format json",
                    }
                )

                api_response = {"action": "move", "obj_moved_id": 0, "pos": "0;0"}

            self.data = self.generate_JSON(objects, iou)

            LLMInteraction(api_response, my_objects)

        self.screen.fill(self.color["background"])

        for obj in objects:
            if obj.isMoving:
                obj.moveLinear()

            obj.draw()

        iou_text = self.font.render(
            f"Objetivo Concluído: {iou * 100:.2f} %", True, (0, 0, 0)
        )
        text_rect = iou_text.get_rect(center=(self.config["screen"]["width"] // 2, 25))
        self.screen.blit(iou_text, text_rect)

        pygame.display.flip()
        self.clock.tick(self.fps)

        return [[*my_obj.position, my_obj.type] for my_obj in my_objects]

    def close(self):
        pygame.quit()
