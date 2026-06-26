import datetime
import json
import os
import time

from game.analysis.plotter import plot_grid


class SessionLogger:
    def __init__(self, timestamp: str, player_colors: tuple[str, ...], log_base_folder="LOGS"):
        log_base_folder = os.path.join(log_base_folder, timestamp)
        os.makedirs(log_base_folder, exist_ok=True)
        self.timestamp = timestamp
        self.color = player_colors

        self.log_file_path = os.path.join(log_base_folder, "game_events.jsonl")
        self.log_metadata_path = os.path.join(log_base_folder, "game_metadata.json")
        self.log_nature_path = os.path.join(log_base_folder, "game_players.jsonl")

        self.start_time = time.perf_counter()
        self.last_progress_time = None
        self.last_progress_value = None

    def log_player(self, player_id: int, name: str = "LLM"):
        full_data = {"id": player_id, "color": self.color[player_id], "name": name}

        with open(self.log_nature_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(full_data, ensure_ascii=False) + "\n")

    def log_metadata(self, metadata: dict):
        full_metadata = {
            "session_start_timestamp": self.start_time,
            "date": self.timestamp,
            **metadata,
        }
        with open(self.log_metadata_path, "w", encoding="utf-8") as file:
            file.write(json.dumps(full_metadata, indent=4, ensure_ascii=False) + "\n\n")

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

        with open(self.log_file_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(event_entry, ensure_ascii=False) + "\n")

    def process_data(self):
        plot_grid(self.log_file_path)
