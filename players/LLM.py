import os
import json
import pygame
import datetime

from LLM.agent import *

from players.motion import *
from utils.colision import *

class LLM_PLAYER:
    def __init__(self, source="local"):
        self.source = source

        self.Thinker = Agent_Thinker(source)
        self.Player = Agent_Player(source)

        self.logger = Logger()
        self.logger.log_metadata([self.Thinker, self.Player])
        self.turn_counter = 0

    def LLMInteraction(self, _, my_objects):
        self.turn_counter += 1

        interpretation = self.Thinker.think("data")
        command = self.Player.play(interpretation)

        self.logger.log_turn(self.turn_counter, self.Thinker.name, self.Thinker.payload, interpretation)
        self.logger.log_turn(self.turn_counter, self.Player.name, self.Player.payload, command)

        obj = my_objects[command["object_id"]]

        if command["action"] == "move":
            return move_object(obj, command["dx"], command["dy"], my_objects)

        elif command["action"] == "rotate":
            rotate_object(obj)
            return True

# --------------------------------------------------------------------------------------------

class Logger:
    def __init__(self, log_base_folder: str = "LLM/logs"):
        timestamp = datetime.datetime.now().strftime('%d_%m_%H_%M_%S')
        self.log_file_path = os.path.join(log_base_folder, f'{timestamp}_log.json')
        
        os.makedirs(log_base_folder, exist_ok=True)
        
        self.log_data = {
            "metadata": {},
            "turns": {}
        }

    def log_metadata(self, agents):
        self.log_data["metadata"] = {
            "session_start_time": datetime.datetime.now().isoformat(),
            "agent_configs": [
                {
                    "name": agent.name,
                    "class": agent.__class__.__name__,
                    "llm_source": agent.llm_source,
                    "model": agent.model
                }
                for agent in agents
            ]
        }
        self._save_to_file()

    def log_turn(self, turn_number: int, agent_name: str, payload: str, response: dict):
        turn_key = f"turn_{turn_number}"
        
        if turn_key not in self.log_data["turns"]:
            self.log_data["turns"][turn_key] = {}
        
        self.log_data["turns"][turn_key][agent_name] = {
            "payload": payload,
            "response": response
        }
        self._save_to_file()
        print(f"Log da rodada {turn_number} para o agente '{agent_name}' salvo.")

    def _save_to_file(self):
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.log_data, f, indent=4, ensure_ascii=False)