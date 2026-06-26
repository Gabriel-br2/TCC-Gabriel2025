import json
import os
import re


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


class LLMSessionLogger:
    def __init__(self, timestamp, client_id, log_base_folder="LOGS"):
        log_base_folder = os.path.join(log_base_folder, f"{timestamp}")
        os.makedirs(log_base_folder, exist_ok=True)

        log_llm = os.path.join(log_base_folder, "LLM_interaction")
        os.makedirs(log_llm, exist_ok=True)
        self.log_file_path = os.path.join(log_llm, f"player_{client_id}_log.json")
        self.log_file_llm_metadata = os.path.join(
            log_llm, f"player_{client_id}_data.json"
        )

        self.client_id = client_id
        self.log_data = {"turns": {}}

    def log_metadata(self, agents):
        import datetime

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

        with open(self.log_file_llm_metadata, "w", encoding="utf-8") as file:
            file.write(json.dumps(full_metadata, indent=4, ensure_ascii=False) + "\n\n")

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
        with open(self.log_file_path, "w", encoding="utf-8") as file:
            json.dump(self.log_data, file, indent=4, ensure_ascii=False)
