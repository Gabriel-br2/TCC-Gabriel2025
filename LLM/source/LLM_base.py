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

        self.source_CLASS = OPENROUNTER_API if llm_source == "api" else OLLAMA_APP
        self.source = self.source_CLASS(model)

        self._set_initial_context()
        self._json_pattern = self._get_return_json_pattern()

    def _set_initial_context(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def _get_return_json_pattern(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def generate_payload(self, msg: dict, msg_tag: str):
        self.payload = f"<context>\n{self.context}\n"
        self.payload += "Follow the bellow json to answer:\n"
        self.payload += f"{json.dumps(self._json_pattern, indent=2)}\n"
        self.payload += "</context>\n"
        self.payload += f"<{msg_tag}>\n"
        self.payload += f"{json.dumps(msg, indent=2)}\n"
        self.payload += f"</{msg_tag}>\n"

    def request(self, path=None):
        print(f"[{self.name}]: {self.payload}")
        if self.payload is None:
            raise ValueError(
                "The payload was not generated. Call the generate_payload() method first."
            )
        return self.source.request(self.payload, path)
