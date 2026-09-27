from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from game.llm.source.api import *
from game.llm.agents.gamer_agent      import GameAgent, GameDecision
from game.llm.agents.thinker_agent    import ThinkerAgent, ThinkingResult
from game.llm.agents.summarizer_agent import SummarizerAgent, SummaryResult, GameMemory
from game.llm.agents.observer_agent   import AgentEvent, AgentObserver, Observer


@dataclass
class GameContext:
    game_name       : str
    rules           : str
    state           : str = ""
    valid_actions   : list[str] = field(default_factory=list)
    strategy        : Optional[str] = None
    context_summary : str = ""
    history         : list[str] = field(default_factory=list)
    _lock           : threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def set_strategy(self, value: str) -> None:
        with self._lock:
            self.strategy = value

    def set_context_summary(self, value: str) -> None:
        with self._lock:
            self.context_summary = value

    def snapshot(self) -> tuple[Optional[str], str]:
        with self._lock:
            return self.strategy, self.context_summary


_STOP = object()


class GameOrchestrator:
    def __init__(
        self,
        gamer    : GameAgent,
        thinker  : Optional[ThinkerAgent]  = None,
        memory   : Optional[GameMemory]    = None,
        rules    : str                     = "",
        observer : Optional[AgentObserver] = None,
        budget   : Optional[SessionBudget] = None,
    ) -> None:

        self.gamer    = gamer
        self.thinker  = thinker
        self.memory   = memory
        self.rules    = rules
        self.observer = observer
        self.budget   = budget

        self.ctx = GameContext(
            game_name=getattr(gamer, "game_name", ""),
            rules=rules)

        self._thinker_queue : "queue.Queue" = queue.Queue()
        self._memory_queue  : "queue.Queue" = queue.Queue()
        self._threads       : list[threading.Thread] = []
        self._turn_counter  : int = 0

    def start(self) -> None:
        if self.thinker is not None:
            t = threading.Thread(target=self._thinker_worker, daemon=True, name="thinker")
            t.start()
            self._threads.append(t)

        if self.memory is not None:
            t = threading.Thread(target=self._memory_worker, daemon=True, name="summarizer")
            t.start()
            self._threads.append(t)

    def stop(self, timeout: float = 10.0) -> None:
        if self.thinker is not None:
            self._thinker_queue.put(_STOP)
        if self.memory is not None:
            self._memory_queue.put(_STOP)
        for t in self._threads:
            t.join(timeout=timeout)

    def __enter__(self) -> "GameOrchestrator":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()

    def _notify(self, event: AgentEvent) -> None:
        if self.observer is None:
            return
        try:
            self.observer.notify(event)
        except Exception as e:
            print(f"[observer] falha ao notificar: {e}")

    def _consume_recent_expenses(self, before_len: int) -> tuple[float, list[ExpenseRecord]]:
        if self.budget is None:
            return 0.0, []

        new_records = self.budget.history[before_len:]
        total_cost = sum(r.expense for r in new_records)
        return total_cost, new_records

    def _track_call(
        self,
        agent         : str,
        turn          : Optional[int],
        in_value      : str,
        fn            : Callable[[], Any],
        out_extractor : Callable[[Any], Optional[str]] = lambda r: str(r),
        score_extractor: Callable[[Any], Optional[float]] = lambda r: None, 
        reraise       : bool = False,
    ) -> Any:
      
        start = time.perf_counter()
        before_len = len(self.budget.history) if self.budget is not None else 0

        result: Any = None
        out_value: str = ""
        error: Optional[str] = None
        score: Optional[float] = None
        parameters: Optional[dict[str, Any]] = None
        value: float = 0.0

        try:
            result = fn()
            raw_out = out_extractor(result)
            out_value = raw_out if raw_out is not None else ""
            score = score_extractor(result)
            return result
        except (BudgetExceededError, APIError) as e:
            error = f"{type(e).__name__}: {e}"
            print(f"[{agent}] {error}")
            if reraise:
                raise
            return None
        finally:
            
            self._notify(AgentEvent(
                agent=agent,
                in_value=in_value,
                out_value=out_value,
                duration=time.perf_counter() - start,
                timestamp=time.time(),
                turn=turn,
                score=score,
                error=error,
            ))

    def _thinker_worker(self) -> None:
        thinker = self.thinker
        assert thinker is not None
        while True:
            item = self._thinker_queue.get()
            if item is _STOP:
                return
            turn, state = item
            _, context_summary = self.ctx.snapshot()

            thinking: Optional[ThinkingResult] = self._track_call(
                agent="thinker",
                turn=turn,
                in_value=state,
                fn=lambda: thinker.think(
                    game_name=self.ctx.game_name,
                    rules=self.ctx.rules,
                    state=state,
                    context=context_summary,
                ),
                out_extractor=lambda r: r.strategy,
            )
            if thinking is not None:
                self.ctx.set_strategy(thinking.strategy)
                print(f"[thinker] new strategy: {thinking.strategy}")

    def _memory_worker(self) -> None:
        memory = self.memory
        assert memory is not None
        while True:
            item = self._memory_queue.get()
            if item is _STOP:
                return
            turn, turn_text = item

            def _update_memory() -> str:
                memory.add_turn(turn_text)
                return memory.context_for_prompt()

            new_context: Optional[str] = self._track_call(
                agent="summarizer",
                turn=turn,
                in_value=turn_text,
                fn=_update_memory,
                out_extractor=lambda _r: memory.summary,
            )
            if new_context is not None:
                self.ctx.set_context_summary(new_context)
                print(f"[summarizer] updated summary: {memory.summary}")

    def submit_turn(self, state: str) -> int:
        self._turn_counter += 1
        turn = self._turn_counter

        self.ctx.state = state
        self.ctx.history.append(state)

        if self.thinker is not None:
            self._thinker_queue.put((turn, state))
        if self.memory is not None:
            self._memory_queue.put((turn, state))

        return turn

    def play_turn(self, state: str, valid_actions: list[str]) -> GameDecision:
        turn = self.submit_turn(state)
        self.ctx.valid_actions = valid_actions
        strategy, context_summary = self.ctx.snapshot()

        decision: GameDecision = self._track_call(
            agent="gamer",
            turn=turn,
            in_value=json.dumps(
                {"state": state, "valid_actions": valid_actions},
                ensure_ascii=False,
            ),
            fn=lambda: self.gamer.decide(
                state,
                valid_actions,
                strategy=strategy,
                context=context_summary,
            ),
            out_extractor=lambda r: r.action,
            score_extractor=lambda r: getattr(r, "confidence", None),
            reraise=True,
        )
        return decision










if __name__ == "__main__":
    client = OpenRouterClient(api_key="key-here", title="game-agent")
    retry = Retry(client)
    budget = SessionBudget(credit_limit=0.10)
    guard = BudgetGuard(retry, budget)

    rules = (
        "3x3 board, cells numbered from 1 to 9 (left->right, top->bottom). "
        "You are analyzing for player 'O'. The opponent is 'X'. "
        "First to align 3 symbols wins."
    )

    gamer = GameAgent(
        client=guard,
        model="typesafe/jev-1.13",
        game_name="discover the plot",
        prompt_path=Path("llm/prompts/gamer.md"),
        rules=rules,
    )

    thinker = ThinkerAgent(
        client=guard,
        model="openai/gpt-4o",
        prompt_path=Path("llm/prompts/thinker.md"),
    )

    summarizer = SummarizerAgent(
        client=guard,
        model="openai/gpt-4o-mini",
        prompt_path=Path("llm/prompts/summarizer.md"),
    )

    memory = GameMemory(
        game_name="discover the plot",
        summarizer=summarizer,
        max_raw_chars=200,
        keep_last_n_turns=2,
    )

    observer = Observer(
        timestamp="20231010_120000", 
        client_id="player-1", 
        log_base_folder="LOGS"
    )

    orchestrator = GameOrchestrator(
        gamer=gamer,
        thinker=thinker,
        memory=memory,
        rules=rules,
        observer=observer,
        budget=budget,
    )

    states_and_actions = [
        ("1:X 2:O 3:_\n"
         "4:_ 5:O 6:_\n"
         "7:X 8:_ 9:_",
         
         ["3", "4", "6", "8", "9"]),
    ]

    with orchestrator:
        for state, valid_actions in states_and_actions:
            try:
                decision = orchestrator.play_turn(state, valid_actions)
                print(f"[gamer] chosen action: {decision.action}")
            except BudgetExceededError as e:
                print(f"Budget Exceeded: {e}")
                break
            except APIError as e:
                print(f"API Error: {e}")


