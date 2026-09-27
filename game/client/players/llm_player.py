from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Optional

from game.llm.source.api              import BudgetExceededError, APIError, SessionBudget
from game.llm.agent_orchestrator      import GameOrchestrator
from game.llm.agents.gamer_agent      import GameAgent, GameDecision
from game.llm.agents.thinker_agent    import ThinkerAgent
from game.llm.agents.observer_agent   import Observer
from game.llm.agents.summarizer_agent import SummarizerAgent, GameMemory

from game.client.players.motion import move_object, rotate_object
from game.client.logger import LLMSessionLogger 

colors = ["blue", "pink", "yellow", "cyan"]


class LLMPlayer:
    def __init__(
        self,
        timestamp : str,
        client_id : str,
        cfg       : dict,
        client    : Any,
        rules     : str = "",
        source    : str = "local",
        budget    : Optional[SessionBudget] = None,
    ) -> None:
        self.source    = source
        self.client_id = client_id
        self.cfg       = cfg

        game_name = f"player-{client_id}"

        gamer = GameAgent(
            client      = client,
            model       = os.getenv("PLAYER_MODEL_NAME", "openai/gpt-4o-mini"),
            game_name   = game_name,
            prompt_path = Path("game/llm/prompts/gamer.md"),
            rules       = rules,
        )

        thinker = ThinkerAgent(
            client      = client,
            model       = os.getenv("THINKER_MODEL_NAME", "openai/gpt-4o-mini"),
            prompt_path = Path("game/llm/prompts/thinker.md"),
        )

        summarizer = SummarizerAgent(
            client      = client,
            model       = os.getenv("SUMMARIZER_MODEL_NAME", "openai/gpt-4o-mini"),
            prompt_path = Path("game/llm/prompts/summarizer.md"),
        )

        memory = GameMemory(
            game_name         = game_name,
            summarizer        = summarizer,
            max_raw_chars     = cfg.get("max_raw_chars", 200),
            keep_last_n_turns = cfg.get("keep_last_n_turns", 2),
        )

        observer = Observer(
            timestamp       = timestamp,
            client_id       = client_id,
            log_base_folder = cfg.get("log_base_folder", "LOGS"),
        )

        self.orchestrator = GameOrchestrator(
            gamer    = gamer,
            #thinker  = thinker,
            #memory   = memory,
            rules    = rules,
            observer = observer,
            budget   = budget,
        )

        self.orchestrator.start()

        self.other_objects = None
        self.my_objects    = None
        self.score         = None
        self.last_position = None


    def plot_objects(self, other_objects, my_objects, delta_calc=False):
        position = {}

        for i in other_objects:
            player_key = f"player_{colors[i.id].upper()}"
            if player_key not in position:
                position[player_key] = {}

            shape = i.shape_name
            p1, p2, a = i.position
            a = a % 360

            position[player_key][f"object_{i.obj_id}"] = {
                "type": shape,
                "pos": [p1, p2],
                "rot": a,
            }

        return position


    def objective_reached(self) -> None:
        d = self.score if self.score is not None and self.score >= 95 else 95
        positions = self.plot_objects(self.other_objects, self.my_objects)

        final_state = json.dumps(
            {"objective_reached": True, "score": d, "positions": positions},
            ensure_ascii=False,
        )

        self.orchestrator.submit_turn(final_state)


    def llm_interaction(self, other_objects, my_objects, score, is_active=None):
        if is_active is not None and not is_active():
            return False

        self.other_objects = other_objects
        self.my_objects = my_objects
        self.score = score

        previous_positions = self.plot_objects(other_objects, my_objects)

        state = json.dumps(
            {"actual_score": score * 100, "actual_position": previous_positions},
            ensure_ascii=False,
        )

        MOVE_VALUES = [-20, -10, -5, 5, 10, 20]
        valid_actions = []

        for obj in my_objects:
            for dx in MOVE_VALUES:
                for dy in MOVE_VALUES:
                    valid_actions.append(
                        f"{obj.obj_id},{dx},{dy}"
                    )

        try:
            decision: GameDecision = self.orchestrator.play_turn(state, valid_actions)
        except BudgetExceededError as e:
            print(f"[LLMPlayer] Budget Exceeded: {e}")
            return False
        except APIError as e:
            print(f"[LLMPlayer] API Error: {e}")
            return False

        if is_active is not None and not is_active():
            return False

        command = self._parse_command(decision)
        if command is None:
            return False

        print("COMANDO RECEBIDO:", command)

        try:
            obj = next(
                obj for obj in my_objects
                if obj.obj_id == command["object_id"]
            )

            okay = move_object(
                obj,
                command["dx"],
                command["dy"],
                my_objects,
                self.cfg,
                True
            )

            return okay

        except StopIteration:
            print(
                f"[LLMPlayer] ID de objeto inválido: "
                f"{command['object_id']}"
            )
            return False

    def _parse_command(self, decision: GameDecision) -> Optional[dict]:
        try:
            object_id, dx, dy = decision.action.split(",")

            return {
                "object_id": int(object_id),
                "dx": float(dx),
                "dy": float(dy),
            }

        except (ValueError, AttributeError) as e:
            print(f"[LLMPlayer] Ação inválida recebida do Jev: {e}")
            return None

    def close(self) -> None:
        self.orchestrator.stop()

    def __enter__(self) -> "LLMPlayer":
        return self

    def __exit__(self, *exc) -> None:
        self.close()