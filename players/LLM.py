import pygame

from LLM.agent import *
from players.motion import *
from utils.colision import *
from utils.logger import Logger_LLM

colors = ["blue", "pink", "yellow", "cyan"]


def add_key_value_as_first(dictionary, key_to_add, value_to_add):
    new_ordered_dict = {key_to_add: value_to_add}
    for k, v in dictionary.items():
        new_ordered_dict[k] = v

    dictionary.clear()
    dictionary.update(new_ordered_dict)

    return dictionary


def add_to_dict(dictionary, key, value, summaryse):
    if dictionary is None:
        dictionary = {}

    dictionary[str(key)] = value

    if len(dictionary) >= 5:
        excluded = {}
        for _ in range(3):
            k = list(dictionary.keys())[0]
            v = list(dictionary.values())[0]
            excluded[k] = v
            dictionary.pop(k)

        last_excluded = int(k.split("_")[1])

        resume = summaryse.summary(excluded)
        return add_key_value_as_first(dictionary, f"turns_1_to_{last_excluded}", resume)
    return dictionary


class LLM_PLAYER:
    def __init__(self, timestamp, client_id, cfg, source="local", memory_path=None):
        self.source = source

        self.Thinker = Agent_Thinker(client_id, source, memory_path)
        self.Player = Agent_Player(client_id, source, memory_path)
        self.Summary = Agent_summary(client_id, source)

        self.turn_counter = self.Thinker.last_turn

        self.logger = Logger_LLM(timestamp, client_id)
        self.logger.log_metadata([self.Thinker, self.Player])
        self.cfg = cfg

        self.client_id = client_id
        self.other_objects = None
        self.my_objects = None
        self.score = None
        self.last_position = None

    def objective_reached(self):
        d = self.score if self.score is not None and self.score >= 95 else 95
        positions = self.plot_objects(self.other_objects, self.my_objects)

        self.Thinker.objective_reached(self.turn_counter, d, positions)
        self.Player.objective_reached(self.turn_counter, d, positions)
        # self.turn_counter = 0

    def plot_objects(self, other_objects, my_objects, delta_calc=False):
        position = {}

        for i in other_objects:
            if True:  # self.client_id != i.id:
                if f"player_{colors[i.id].upper()}" not in position:
                    position[f"player_{colors[i.id].upper()}"] = {}

                shape = i.shape_name
                p1, p2, a = i.position
                a = a % 360

                position[f"player_{colors[i.id].upper()}"][f"object_{i.obj_id}"] = {
                    "type": shape,
                    "pos": [p1, p2],
                    "rot": a,
                }

        return position

    def LLMInteraction(self, other_objects, my_objects, score):
        self.other_objects = other_objects
        self.my_objects = my_objects
        self.score = score

        self.turn_counter += 1
        self.Thinker.insert_score_data(self.turn_counter, score)
        self.Player.insert_score_data(self.turn_counter, score)

        previous_positions = self.plot_objects(other_objects, my_objects)

        interpretation = self.Thinker.think(
            {"actual score": score * 100, "actual position": previous_positions}
        )
        command = self.Player.play(interpretation)

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

        for key, value in command.items():
            if isinstance(value, list):
                try:
                    i = int(value[0])
                except ValueError:
                    i = value[0]
                except TypeError:
                    i = value[0]
                except IndexError:
                    i = None
            else:
                i = value

            command[key] = i

        print("INTERPREATAÇÂO RECEBIDA:", interpretation)
        print("COMANDO RECEBIDO:", command)

        try:
            obj = my_objects[command["object_id"]]
            okay = False

            if command["action"] == "move":
                if command["x"] in [None, "None", "Null", "null"]:
                    command["x"] = 0

                if command["y"] in [None, "None", "Null", "null"]:
                    command["y"] = 0

                okay = move_object(
                    obj, command["x"], command["y"], my_objects, self.cfg, True
                )

            elif command["action"] == "rotate":
                rotate_object(obj)
                okay = True

            positions = self.plot_objects(other_objects, my_objects, True)

            new_memory = {
                "previous positions": previous_positions,
                "previous score": f"{score*100}%",
                "interpretation from agent thinker": interpretation,
                "movements from agent player": command,
                "result positions": positions,
                "result score": None,
            }

            self.Thinker.memory_save(
                self.turn_counter, add_to_dict, self.Summary, new_memory
            )

            self.Player.memory_save(
                self.turn_counter, add_to_dict, self.Summary, new_memory
            )

            return okay

        except (IndexError, KeyError):
            error = {
                "error": "Invalid object ID received by player agent, choose a valid number next time."
            }

            self.Thinker.memory_save(
                self.turn_counter, add_to_dict, self.Summary, error
            )

            self.Player.memory_save(self.turn_counter, add_to_dict, self.Summary, error)

            return False
