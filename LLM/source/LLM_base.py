import json
import os

from LLM.source.api import OPENROUNTER_API
from LLM.source.local import OLLAMA_APP


class Base_Agent:
    def __init__(self, agent_name: str, llm_source: str = "local", model: str = None):
        self.name = agent_name
        self.payload = None
        self.context = ""
        self.llm_source = llm_source
        self.model = model
        self.memory = {}

        self.source_CLASS = OPENROUNTER_API if llm_source == "api" else OLLAMA_APP
        self.source = self.source_CLASS(model)

        self._set_initial_context()
        self._json_pattern = self._get_return_json_pattern()

    def _set_initial_context(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def _get_return_json_pattern(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def memory_save(self, turn, positions, interpretations, movements, score):

        new_memory = {
            "interpretation from agent thinker": interpretations,
            "movements from agent player": movements,
            "result positions": positions,
            "score in this turn": score,
        }

        self.memory[f"turn_{turn}"] = new_memory

    def generate_payload(self, msg: dict, msg_tag: str):
        self.payload = f"<context>\n{self.context}\n"
        self.payload += "Follow the bellow json to answer:\n"
        self.payload += f"{json.dumps(self._json_pattern, indent=2)}\n"
        self.payload += "</context>\n"
        self.payload += "<memory>\n"
        self.payload += f"{json.dumps(self.memory, indent=2)}\n"
        self.payload += "</memory>\n"
        self.payload += f"<{msg_tag}>\n"
        self.payload += f"{json.dumps(msg, indent=2)}\n"
        self.payload += f"</{msg_tag}>\n"

    def request(self, path=None):
        if self.name == "THINKER":
            return {
                "attention_focus": [
                    "Observing the initial moves where Agent 2 placed a cube at (0,0,0) and Agent 3 moved a sphere. The randomness suggests they are in the early exploration phase."
                ],
                "theory_of_mind_inference": [
                    "Agent 2 appears to be trying to mark a location. Agent 1 and 3 are still uncertain. No clear pattern yet."
                ],
                "retention_hypothesis": [
                    "The hidden pose might be a specific coordinate but we are not there yet."
                ],
                "intended_outcome": "Continue observing initial moves to gather more data before deciding to explore or exploit.",
            }

        # elif self.name == "PLAYER":
        #    return {'action': 'move', 'object_id': 0, 'dx': 10, 'dy': -5
        #        }

        # return None

        if self.payload is None:
            raise ValueError(
                "The payload was not generated. Call the generate_payload() method first."
            )
        return self.source.request(self.payload, path)
