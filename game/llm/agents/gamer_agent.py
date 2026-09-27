from dataclasses import dataclass
from typing import Union
from pathlib import Path

from game.llm.source.api import (
    DecisionAdapter,
    OpenRouterClient,
    Retry,
    BudgetGuard,
    SessionBudget,
    APIError,
    BudgetExceededError,
)

ClientLike = Union[OpenRouterClient, Retry, BudgetGuard]
MOVE_VALUES = [-20, -10, 0, 10, 20]

@dataclass
class GameDecision:
    action        : str
    cost          : float
    confidence    : float | None
    probabilities : dict[str, float]


class GameAgent:
    def __init__(
        self,
        client        : ClientLike,
        game_name     : str,
        rules         : str,
        model         : str,
        prompt_path   : Path | None = None,
        question_name : str  | None = "action",
    ):
        self._client       = client
        self.rules         = rules
        self.model         = model
        self.game_name     = game_name
        self.question_name = question_name or "action"

        prompt_path = prompt_path or Path("llm/prompts/gamer.md")
        self.base_prompt = prompt_path.read_text(encoding="utf-8")

        self.instructions  = self._system_prompt(game_name, rules)

    def _system_prompt(self, game_name: str, rules: str) -> str:
        return self.base_prompt.format(
            game_name=game_name,
            rules=rules
        )

    def _build_state(self, state: str | dict, context: str | None = None) -> dict:
        payload = {
            "game"          : self.game_name,
            "rules"         : self.rules,
            "current_state" : state,
        }
        
        if context:
            payload["context"] = context
        return payload

    def _build_questions(
        self,
        valid_actions: list[str],
        action_descriptions: dict[str, str] | None = None,
        strategy: str | None = None,
    ) -> dict:

        instructions = self.instructions
        if strategy:
            instructions = (
                f"{instructions}\n\n"
                f"Strategic guidance from your analyst (use it, but you have "
                f"the final call):\n{strategy}"
            )

        descriptions = action_descriptions or {}
        criteria = {a: descriptions.get(a, a) for a in valid_actions}
        return {
            self.question_name: {
                "type"         : "choice",
                "instructions" : instructions,
                "criteria"     : criteria,
            }
        }

    def decide(
        self,
        state               : str | dict,
        valid_actions       : list[str],
        action_descriptions : dict[str, str] | None = None,
        strategy            : str | None = None,
        context             : str | None = None,
    ) -> GameDecision:
        
        if not valid_actions:
            raise ValueError("valid_actions can not be empty.")
        if len(valid_actions) > 255:
            raise ValueError("Jev's Choice accepts at most 255 options.")

        payload = {
            "model": self.model,
            "state": self._build_state(state, context=context),
            "questions": self._build_questions(valid_actions, action_descriptions, strategy=strategy),
        }

        raw = self._client.post("alpha/decisions", payload)
        response = DecisionAdapter(raw)

        return GameDecision(
            action=response.choice(self.question_name),
            confidence=response.confidence(self.question_name),
            probabilities=response.probabilities(self.question_name),
            cost=response.cost,
        )





if __name__ == "__main__":
    client = OpenRouterClient(api_key="key-here", title="game-agent")
    retry = Retry(client)
    budget = SessionBudget(credit_limit=0.10)
    guard = BudgetGuard(retry, budget)

    agent = GameAgent(
        client=guard,
        model="typesafe/jev-1.13",
        game_name="Tic-Tac-Toe",
        prompt_path=Path("llm/prompts/gamer.md"),
        rules=(
            "3x3 board, cells numbered from 1 to 9 (left->right, top->bottom). "
            "You are player 'O'. The opponent is 'X'. First to align 3 symbols wins."
        ),
    )

    state = "1:X 2:O 3:_" \
          "\n4:_ 5:O 6:_" \
          "\n7:X 8:_ 9:_"
    valid_actions = ["3", "4", "6", "8", "9"]

    strategy = (
        "X is one move from winning at cell 7-8-9 diagonal check isn't live, "
        "but X threatens column 1 (1-4-7 has two X). Block at 4? No, 4 is "
        "already O. Prioritize taking 9 to open a fork with 3-5-9 or 9-5-1."
    )

    try:
        decision = agent.decide(state, valid_actions, strategy=strategy)

        print(f"Chosen action: {decision.action}")
        print(f"Confidence: {decision.confidence}")
        print(f"Probabilities: {decision.probabilities}")
        print(f"Cost of this call: USD {decision.cost:.6f}")
        print(budget.summary())
    except BudgetExceededError as e:
        print(f"Session interrupted: {e}")
    except APIError as e:
        print(f"API Error: {e}")