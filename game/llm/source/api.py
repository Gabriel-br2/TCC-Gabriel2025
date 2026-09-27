import os
import time
import threading
import pandas as pd

import requests
from typing import Any, ClassVar
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod

CSV_PATH = "LOGS/expenses.csv"

class APIError(Exception):
    pass


class BudgetExceededError(APIError):
    pass


class OpenRouterClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 api_key: str | None = None,
                 title:   str | None = None,
                 base_url: str = "https://openrouter.ai/api",
                 ):

        if getattr(self, "_initialized", False):
            return

        self.api_key  = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.title    = title or os.environ.get("TITLE")
        self.base_url = base_url
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type" :  "application/json",
        })

        self._initialized = True

    def post(self, endpoint: str, payload: dict) -> dict:

        print("@@@@@@@@@@@@@@@@@@@", payload)

        url = f"{self.base_url}/{endpoint}"
        response = self.session.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()

    def get(self, endpoint: str) -> dict:
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        return response.json()


class RequestBuilder:
    def __init__(self, model: str):
        self._payload = {"model": model, "messages": []}

    def add_system(self, content: str) -> "RequestBuilder":
        self._payload["messages"].append({"role": "system", "content": content})
        return self

    def add_user(self, content: str) -> "RequestBuilder":
        self._payload["messages"].append({"role": "user", "content": content})
        return self

    def add_assistant(self, content: str) -> "RequestBuilder":
        self._payload["messages"].append({"role": "assistant", "content": content})
        return self

    def temperature(self, value: float) -> "RequestBuilder":
        self._payload["temperature"] = value
        return self

    def max_tokens(self, value: int) -> "RequestBuilder":
        self._payload["max_tokens"] = value
        return self

    def track_usage(self) -> "RequestBuilder":
        self._payload["usage"] = {"include": True}
        return self

    def build(self) -> dict:
        return self._payload


class Retry:
    def __init__(self, client: OpenRouterClient, max_retries: int = 3, base_delay: float = 1.0):
        self._client = client
        self.title = client.title
        self._max_retries = max_retries
        self._base_delay = base_delay

    def post(self, endpoint: str, payload: dict) -> dict:
        last_error = None
        for attempt in range(self._max_retries):
            try:
                return self._client.post(endpoint, payload)
            except requests.exceptions.RequestException as exc:
                last_error = exc
                wait = self._base_delay * (2 ** attempt)
                time.sleep(wait)
        raise APIError(f"Failed after {self._max_retries} attempts: {last_error}") from last_error

    def get(self, endpoint: str) -> dict:
        last_error = None
        for attempt in range(self._max_retries):
            try:
                return self._client.get(endpoint)
            except requests.exceptions.RequestException as exc:
                last_error = exc
                wait = self._base_delay * (2 ** attempt)
                time.sleep(wait)
        raise APIError(f"Failed after {self._max_retries} attempts: {last_error}") from last_error


class RequestFactory:
    @staticmethod
    def create(kind: str, **kwargs) -> dict:
        if kind == "chat":
            builder = RequestBuilder(kwargs["model"])
            if "system" in kwargs:
                builder.add_system(kwargs["system"])
            builder.add_user(kwargs["prompt"])
            builder.track_usage()
            return builder.build()
        else:   
            raise ValueError(f"unknown request kind: {kind}") 


class ResponseAdapter:
    def __init__(self, raw_response: Any):
        self._raw = raw_response

    @property
    def text(self) -> str:
        return self._raw["choices"][0]["message"]["content"]

    @property
    def model_used(self) -> str:
        return self._raw.get("model", "desconhecido")

    @property
    def tokens_used(self) -> int:
        return self._raw.get("usage", {}).get("total_tokens", 0)

    @property
    def cost(self) -> float:
        return self._raw.get("usage", {}).get("cost", 0.0) or 0.0


class DecisionAdapter:

    def __init__(self, raw: dict):
        self._raw = raw

    def _answer(self, question: str) -> dict:
        try:
            return self._raw["answers"][question]
        except KeyError as exc:
            raise APIError(
                f"'{question}': {self._raw}"
            ) from exc

    def choice(self, question: str) -> str:
        return self._answer(question)["choice"]

    def confidence(self, question: str) -> float | None:
        return self._answer(question).get("confidence")

    def probabilities(self, question: str) -> dict[str, float]:
        return self._answer(question).get("probabilities", {})

    @property
    def model_used(self) -> str:
        return self._raw.get("model", "unknown")

    @property
    def cost(self) -> float:
        return self._raw.get("usage", {}).get("cost", 0.0) or 0.0


@dataclass
class ExpenseRecord:
    expense           : float
    title             : str 
    model             : str | None = None
    prompt_tokens     : int | None = None
    completion_tokens : int | None = None
    date: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    leftover: float | None = None

    _current_leftover: ClassVar[float | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __post_init__(self):
        with ExpenseRecord._lock:
            if ExpenseRecord._current_leftover is None:
                raise RuntimeError("Call Expense 'startSession' before creating records.")
            ExpenseRecord._current_leftover -= self.expense
            self.leftover = ExpenseRecord._current_leftover
            self._save()

    @classmethod
    def startSession(cls, budget: float):
        with cls._lock:
            cls._current_leftover = budget

    def _save(self):
        df = pd.DataFrame([asdict(self)])
        existe = os.path.isfile(CSV_PATH)
        df.to_csv(CSV_PATH, mode="a", header=not existe, index=False)


class SessionBudget:
    def __init__(self, credit_limit: float):
        self.credit_limit = credit_limit
        self.total_expenditure = 0.0
        self.history: list[ExpenseRecord] = []
        self._lock = threading.Lock()

    def can_spend(self) -> bool:
        with self._lock:
            return self.total_expenditure < self.credit_limit

    def register(self, expense: float, **details) -> None:
        with self._lock:
            self.total_expenditure += expense
            self.history.append(ExpenseRecord(expense=expense, **details))

    def leftover(self) -> float:
        with self._lock:
            return max(0.0, self.credit_limit - self.total_expenditure)

    def summary(self) -> str:
        with self._lock:
            return (
                f"Spent: {self.total_expenditure:.6f} / {self.credit_limit:.6f} credits "
                f"({len(self.history)} calls, {max(0.0, self.credit_limit - self.total_expenditure):.6f} remaining)"
            )


class BudgetGuard:
    def __init__(self, client, budget: SessionBudget):
        self._client = client
        self.budget = budget

        info = self._client.get("v1/key")
        budget_remaining = info.get("data",{}).get("limit_remaining",0)
        
        ExpenseRecord.startSession(budget_remaining)

    def post(self, endpoint: str, payload: dict) -> dict:
        if not self.budget.can_spend():
            raise BudgetExceededError(
                f"Limit of {self.budget.credit_limit} credits exceeded in this session. "
                f"{self.budget.summary()}"
            )

        raw = self._client.post(endpoint, payload)

        usage = raw.get("usage", {}) or {}
        expense = usage.get("cost", 0.0) or 0.0
        self.budget.register(
            expense,
            title=self._client.title or "unknown",
            model=raw.get("model"),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

        return raw





if __name__ == "__main__":
    client = OpenRouterClient(
                    api_key="key-here", 
                    title="test"
                  )
    
    retry  = Retry(client)

    budget = SessionBudget(credit_limit=0.05)
    guard  = BudgetGuard(retry, budget)

    questions = [
        "Resume the Singleton pattern in one sentence.",
        "Resume the Observer pattern in one sentence.",
    ]

    for question in questions:
        
        payload = RequestFactory.create(
            kind="chat",
            model="openai/gpt-4o-mini",
            prompt=question,
        )
        
        try:
            raw = guard.post("v1/chat/completions", payload)
            response = ResponseAdapter(raw)
            print(f"[{response.cost:.6f} credits] {response.text}")
        
        except BudgetExceededError as e:
            print(f"Session interrupted: {e}")
            break