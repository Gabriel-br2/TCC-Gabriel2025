import pygame
from LLM.agent import *
from players.motion import *
from utils.colision import *
from utils.logger import Logger_LLM


class LLM_PLAYER:
    def __init__(self, timestamp, client_id, source="local"):
        self.source = source

        self.Thinker = Agent_Thinker(source)
        self.Player = Agent_Player(source)

        self.logger = Logger_LLM(timestamp, client_id)
        self.logger.log_metadata([self.Thinker, self.Player])
        self.turn_counter = 0

    def LLMInteraction(self, other_objects, my_objects, score):
        self.turn_counter += 1

        interpretation = self.Thinker.think("data")
        command = self.Player.play(interpretation)

        print("COMANDO RECEBIDO:", command)

        obj = my_objects[command["object_id"]]

        okay = False
        if command["action"] == "move":
            okay = move_object(obj, command["dx"], command["dy"], my_objects)

        elif command["action"] == "rotate":
            rotate_object(obj)
            okay = True

        positions = {}
        for i in other_objects:
            positions[f"player {i.id} objects"] = i.position
        for k in my_objects:
            positions["my objects"] = i.position

        self.Thinker.memory_save(
            self, self.turn_counter, positions, interpretation, command
        )
        self.Player.memory_save(
            self, self.turn_counter, positions, interpretation, command
        )

        self.logger.log_turn(
            self.turn_counter,
            self.Thinker.name,
            self.Thinker.payload,
            self.Thinker.tag,
            interpretation,
        )
        self.logger.log_turn(
            self.turn_counter,
            self.Player.name,
            self.Player.payload,
            self.Player.tag,
            command,
        )

        return okay
