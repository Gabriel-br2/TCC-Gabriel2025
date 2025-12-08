import json
import os

from LLM.source.api import OPENROUNTER_API
from LLM.source.local import OLLAMA_APP


class Base_Agent:
    def __init__(
        self,
        agent_name: str,
        llm_source: str = "local",
        model: str = None,
        memory: bool = True,
        memory_path: str = None,
    ):
        self.llm_source = llm_source
        self.has_memory = memory
        self.payload = None
        self.context = ""
        self.model = model
        self.name = agent_name
        self.last_score = 0

        self.source_CLASS = OPENROUNTER_API if llm_source == "api" else OLLAMA_APP
        self.source = self.source_CLASS(model)

        self._set_initial_context()
        self._json_pattern = self._get_return_json_pattern()

        if memory_path is not None and os.path.exists(memory_path):
            with open(memory_path) as f:
                data = json.load(f)

            turns = data["turns"]
            last = list(turns.keys())[-1]
            self.memory = turns[last][agent_name]["payload"]["memory"]
            self.last_turn = int(list(self.memory.keys())[-1].split("_")[1])

        else:
            self.memory = {}
            self.last_turn = 0

    def _set_initial_context(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def _get_return_json_pattern(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def objective_reached(self, turn, score, positions):
        self.memory[f"turn_{turn}"] = {
            "score": f"{score}%",
            "result": "Objective reached, restarting the game.",
            "postions": positions,
        }

    def insert_score_data(self, turn, score):
        if self.memory is not None:
            if f"turn_{turn-1}" in self.memory:

                if score > self.last_score:
                    self.last_score = score
                    self.memory[f"turn_{turn-1}"][
                        "result score"
                    ] = f"The increase score was good: {score*100}%"

                else:
                    self.last_score = score
                    self.memory[f"turn_{turn-1}"][
                        "result score"
                    ] = f"The decrease score was bad: {score*100}%"

    def memory_save(self, turn, add_to_dict, Summary, new_memory):
        self.memory = add_to_dict(self.memory, f"turn_{turn}", new_memory, Summary)

    def generate_payload(self, msg: dict, msg_tag: str):
        self.payload = f"<context>\n{self.context}\n"
        self.payload += "Follow the bellow json to answer:\n"
        self.payload += f"{json.dumps(self._json_pattern, indent=2)}\n"
        self.payload += "</context>\n"

        if self.has_memory:
            self.payload += "<memory>\n"
            self.payload += f"{json.dumps(self.memory, indent=2)}\n"
            self.payload += "</memory>\n"

        self.payload += f"<{msg_tag}>\n"
        self.payload += f"{json.dumps(msg, indent=2)}\n"
        self.payload += f"</{msg_tag}>\n"

    def request(self, path=None):
        if self.payload is None:
            raise ValueError(
                "The payload was not generated. Call the generate_payload() method first."
            )
        return self.source.request(self.payload, path)
