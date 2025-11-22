import datetime
import json
import os
import re
import time

from utils.plotter import plot_grid


def payload_to_dict(payload_str):
    pattern = r"<(?P<key>[^>]+)>\s*(?P<value>.*?)\s*</(?P=key)>"

    matches = re.finditer(pattern, payload_str, re.DOTALL)

    result_dict = {}
    for match in matches:
        key = match.group("key")
        value = match.group("value").strip()

        if key == "context":
            continue

        try:
            result_dict[key] = json.loads(value)
        except json.JSONDecodeError:
            result_dict[key] = value

    return result_dict


class Logger_LLM:
    def __init__(self, timestamp, client_id, log_base_folder="LOGS"):
        log_base_folder = os.path.join(log_base_folder, f"{timestamp}")
        os.makedirs(log_base_folder, exist_ok=True)

        log_LLM = os.path.join(log_base_folder, "LLM_interaction")
        os.makedirs(log_LLM, exist_ok=True)
        self.log_file_path = os.path.join(log_LLM, f"player_{client_id}_log.json")
        self.log_file_llm_metadata = os.path.join(
            log_LLM, f"player_{client_id}_data.json"
        )

        self.client_id = client_id
        self.log_data = {"turns": {}}

    def log_metadata(self, agents):
        full_metadata = {
            "session_start_time": datetime.datetime.now().isoformat(),
            "id": self.client_id,
            "agent_configs": [
                {
                    "name": agent.name,
                    "class": agent.__class__.__name__,
                    "llm_source": agent.llm_source,
                    "model": agent.model,
                    "context": agent.context.split("\n"),
                    "pattern": agent._json_pattern,
                }
                for agent in agents
            ],
        }

        with open(self.log_file_llm_metadata, "w", encoding="utf-8") as f:
            json_string = json.dumps(full_metadata, indent=4, ensure_ascii=False)
            f.write(json_string + "\n\n")

    def log_turn(
        self, turn_number: int, agent_name: str, payload: str, tag: str, response: dict
    ):

        payload = payload_to_dict(payload)

        turn_key = f"turn_{turn_number}"

        if turn_key not in self.log_data["turns"]:
            self.log_data["turns"][turn_key] = {}

        self.log_data["turns"][turn_key][agent_name] = {
            "payload": payload,
            "response": response,
        }
        self._save_to_file()
        print(f"Log da rodada {turn_number} para o agente '{agent_name}' salvo.")

    def _save_to_file(self):
        with open(self.log_file_path, "w", encoding="utf-8") as f:
            json.dump(self.log_data, f, indent=4, ensure_ascii=False)


class Logger_data:
    def __init__(self, timestamp, color, log_base_folder="LOGS"):
        log_base_folder = os.path.join(log_base_folder, f"{timestamp}")
        os.makedirs(log_base_folder, exist_ok=True)
        self.timestamp = timestamp
        self.color = color

        self.log_file_path = os.path.join(log_base_folder, "game_events.jsonl")
        self.log_metadata_path = os.path.join(log_base_folder, "game_metadata.json")
        self.log_nature_path = os.path.join(log_base_folder, "game_players.jsonl")

        self.start_time = time.perf_counter()

        self.last_progress_time = None
        self.last_progress_value = None

    def log_player(self, ID, name="LLM"):
        full_data = {"id": ID, "color": self.color[ID], "name": name}

        with open(self.log_nature_path, "a", encoding="utf-8") as f:
            json_string = json.dumps(full_data, ensure_ascii=False)
            f.write(json_string + "\n")

    def log_metadata(self, metadata: dict):
        full_metadata = {
            "session_start_timestamp": self.start_time,
            "date": self.timestamp,
            **metadata,
        }
        with open(self.log_metadata_path, "w", encoding="utf-8") as f:
            json_string = json.dumps(full_metadata, indent=4, ensure_ascii=False)
            f.write(json_string + "\n\n")

    def log_event(self, event_type: str, details: dict):
        current_time = time.perf_counter() - self.start_time

        if event_type == "objective_progress":
            current_progress = details.get("progress", 0) * 100
            rate_of_change = None

            if (
                self.last_progress_time is not None
                and self.last_progress_value is not None
            ):
                delta_progress = current_progress - self.last_progress_value
                delta_time = current_time - self.last_progress_time

                if delta_time > 0:
                    rate_of_change = delta_progress / delta_time

            details["rate_of_change"] = rate_of_change

            self.last_progress_time = current_time
            self.last_progress_value = current_progress

        elif event_type == "Objective reached":
            self.last_progress_time = None
            self.last_progress_value = None

        event_entry = {
            "time_elapsed": current_time,
            "event_type": event_type,
            "details": details,
        }

        with open(self.log_file_path, "a", encoding="utf-8") as f:
            json_string = json.dumps(event_entry, ensure_ascii=False)
            f.write(json_string + "\n")

    def processData(self):
        plot_grid(self.log_file_path)
