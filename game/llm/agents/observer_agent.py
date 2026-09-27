import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Protocol


@dataclass
class AgentEvent:
    agent      : str
    in_value   : str
    out_value  : str
    duration   : float
    timestamp  : float
    turn       : int   | None = None
    score      : float | None = None
    error      : str   | None = None
    parameters : dict[str, Any] | None = None


class AgentObserver(Protocol):
    def notify(self, event: AgentEvent) -> None:
        ...


class Observer(AgentObserver):
    def __init__(self, timestamp, client_id, log_base_folder="LOGS"):
        log_base_folder = os.path.join(log_base_folder, f"{timestamp}")
        os.makedirs(log_base_folder, exist_ok=True)

        log_obs = os.path.join(log_base_folder, "Observer_events")
        os.makedirs(log_obs, exist_ok=True)
        self.log_file_path = os.path.join(log_obs, f"player_{client_id}_events.json")

        self.client_id = client_id
        self.log_data = {"turns": {}, "misc": []}

    def notify(self, event: AgentEvent) -> None:
        event_dict = asdict(event)

        if event.turn is not None:
            turn_key = f"turn_{event.turn}"

            if turn_key not in self.log_data["turns"]:
                self.log_data["turns"][turn_key] = {}

            if event.agent not in self.log_data["turns"][turn_key]:
                self.log_data["turns"][turn_key][event.agent] = []

            self.log_data["turns"][turn_key][event.agent].append(event_dict)
        else:
            self.log_data["misc"].append(event_dict)

        self._save_to_file()

    def _save_to_file(self):
        with open(self.log_file_path, "w", encoding="utf-8") as file:
            json.dump(self.log_data, file, indent=4, ensure_ascii=False)