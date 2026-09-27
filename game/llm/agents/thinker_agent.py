from dataclasses import dataclass
from typing import Union
from pathlib import Path

from game.llm.source.api import (
    OpenRouterClient,
    RequestBuilder,
    ResponseAdapter,
    Retry,
    BudgetGuard,
    APIError,
    SessionBudget,
)

ClientLike = Union[OpenRouterClient, Retry, BudgetGuard]


@dataclass
class ThinkingResult:
    strategy: str
    cost: float
    tokens_used: int


class ThinkerAgent:
    def __init__(
        self,
        client: ClientLike,
        model: str,
        max_tokens: int = 400,
        prompt_path: Path | None = None,
        temperature: float = 0.7,
    ):
        self._client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        path = prompt_path or Path("llm/prompts/thinker.md")
        self.base_prompt = path.read_text(encoding="utf-8")

    def _system_prompt(self, game_name: str, rules: str) -> str:
        return self.base_prompt.format(
            game_name=game_name,
            rules=rules
        )

    def _user_prompt(self, state: str, context: str | None) -> str:
        parts = [f"Actual State:\n{state}"]
        if context:
            parts.append(f"Context of the game so far:\n{context}")
        parts.append("Analyze the position and propose a strategy for the next turns.")
        return "\n\n".join(parts)

    def think(
        self,
        game_name: str,
        rules: str,
        state: str,
        context: str | None = None,
    ) -> ThinkingResult:
        payload = (
            RequestBuilder(self.model)
            .add_system(self._system_prompt(game_name, rules))
            .add_user(self._user_prompt(state, context))
            .temperature(self.temperature)
            .max_tokens(self.max_tokens)
            .track_usage()
            .build()
        )

        raw = self._client.post("v1/chat/completions", payload)
        response = ResponseAdapter(raw)

        return ThinkingResult(
            strategy=response.text.strip(),
            cost=response.cost,
            tokens_used=response.tokens_used,
        )


if __name__ == "__main__":
    client = OpenRouterClient(api_key="key-here", title="game-agent")
    retry = Retry(client)
    budget = SessionBudget(credit_limit=0.10)
    guard = BudgetGuard(retry, budget)

    thinker = ThinkerAgent(
        client=guard, 
        model="openai/gpt-4o", 
        prompt_path=Path("llm/prompts/thinker.md")
    )

    rules = (
        "3x3 board, cells numbered from 1 to 9 (left->right, top->bottom). "
        "You are analyzing for player 'O'. The opponent is 'X'. First to align 3 symbols wins."
    )
    state = "1:X 2:O 3:_\n4:_ 5:O 6:_\n7:X 8:_ 9:_"
    context = (
        "Summary of the game so far: O has two pieces in the center, "
        "X is threatening the bottom-left corner."
    )

    try:
        thinking = thinker.think(game_name="Tic-Tac-Toe", rules=rules, state=state, context=context)
        print("Suggested Strategy:\n", thinking.strategy)
        print(f"\nCost of this call: US$ {thinking.cost:.6f}")
        print(budget.summary())
    except APIError as e:
        print(f"API Error: {e}")