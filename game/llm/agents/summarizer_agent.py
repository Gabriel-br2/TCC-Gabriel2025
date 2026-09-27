from dataclasses import dataclass, field
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
class SummaryResult:
    summary: str
    cost: float
    tokens_used: int


class SummarizerAgent:
    def __init__(
        self,
        client: ClientLike,
        model: str,
        prompt_path: Path | None = None,
        max_tokens: int = 300,
        temperature: float = 0.2,
    ):
        self._client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        path = prompt_path or Path("llm/prompts/summarizer.md")
        self.base_prompt = path.read_text(encoding="utf-8")

    def _system_prompt(self, game_name: str) -> str:
        return self.base_prompt.format(
            game_name=game_name
        )

    def _user_prompt(self, previous_summary: str | None, new_turns: str) -> str:
        parts = []
        if previous_summary:
            parts.append(f"Resumo até agora:\n{previous_summary}")
        parts.append(f"Novos turnos a incorporar:\n{new_turns}")
        return "\n\n".join(parts)

    def summarize(
        self,
        game_name: str,
        new_turns: str,
        previous_summary: str | None = None,
    ) -> SummaryResult:
        payload = (
            RequestBuilder(self.model)
            .add_system(self._system_prompt(game_name))
            .add_user(self._user_prompt(previous_summary, new_turns))
            .temperature(self.temperature)
            .max_tokens(self.max_tokens)
            .track_usage()
            .build()
        )

        raw = self._client.post("v1/chat/completions", payload)
        response = ResponseAdapter(raw)

        return SummaryResult(
            summary=response.text.strip(),
            cost=response.cost,
            tokens_used=response.tokens_used,
        )


@dataclass
class GameMemory:
    game_name: str
    summarizer: SummarizerAgent
    max_raw_chars: int = 4000     
    keep_last_n_turns: int = 3    

    summary: str | None = field(default=None, init=False)
    _raw_turns: list[str] = field(default_factory=list, init=False)

    def add_turn(self, turn_text: str) -> None:
        self._raw_turns.append(turn_text)
        if self._raw_size() > self.max_raw_chars:
            self._compact()

    def _raw_size(self) -> int:
        return sum(len(t) for t in self._raw_turns)

    def _compact(self) -> None:
        keep = self.keep_last_n_turns
        to_summarize = self._raw_turns[:-keep] if len(self._raw_turns) > keep else self._raw_turns
        remaining = self._raw_turns[-keep:] if len(self._raw_turns) > keep else []

        result = self.summarizer.summarize(
            game_name=self.game_name,
            new_turns="\n".join(to_summarize),
            previous_summary=self.summary,
        )
        self.summary = result.summary
        self._raw_turns = remaining

    def context_for_prompt(self) -> str:
        parts = []
        if self.summary:
            parts.append(f"Resumo da partida até aqui:\n{self.summary}")
        if self._raw_turns:
            parts.append("Últimos turnos:\n" + "\n".join(self._raw_turns))
        return "\n\n".join(parts) if parts else "Nenhum histórico ainda."


if __name__ == "__main__":
    client = OpenRouterClient(api_key="key-here", title="game-agent")
    retry = Retry(client)
    budget = SessionBudget(credit_limit=0.10)
    guard = BudgetGuard(retry, budget)

    summarizer = SummarizerAgent(
        client=guard, 
        model="openai/gpt-4o-mini",  
        prompt_path=Path("llm/prompts/summarizer.md")
    )  
    
    memory = GameMemory(
        game_name="Tic-Tac-Toe",
        summarizer=summarizer,
        max_raw_chars=200,
        keep_last_n_turns=2,
    )

    turns = [
        "Turn 1: O played in cell 5 (center). No threats yet.",
        "Turn 2: X played in cell 1. X is aiming for the 1-5-9 diagonal, but 5 belongs to O.",
        "Turn 3: O played in cell 3. O is trying to build the 3-5-7 line.",
        "Turn 4: X played in cell 7, blocking O's 3-5-7 line.",
        "Turn 5: O played in cell 9, with no immediate threat at the moment.",
    ]

    try:
        for turn in turns:
            memory.add_turn(turn)

        print("Current summary:", memory.summary)
        print("\nContext ready for prompt:\n", memory.context_for_prompt())
        print("\n" + budget.summary())
    except APIError as e:
        print(f"API Error: {e}")