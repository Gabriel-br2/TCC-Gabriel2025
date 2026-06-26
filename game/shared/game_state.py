from dataclasses import dataclass
from typing import Any


@dataclass
class GameState:
    """Shared game session snapshot exchanged between server and clients."""

    objects: Any
    iou: float
    cycle_id: int
    is_paused: bool
    connected_players: int
    total_players: int
    reset: bool = False

    def to_broadcast(self) -> dict:
        return {
            "objects": self.objects,
            "reset": self.reset,
            "is_paused": self.is_paused,
            "connected_players": self.connected_players,
            "total_players": self.total_players,
        }

    @classmethod
    def from_broadcast(
        cls,
        payload: dict,
        client_objects: list | None = None,
    ) -> "GameState":
        objects_data = payload.get("objects", {})
        return cls(
            objects=client_objects if client_objects is not None else objects_data,
            iou=objects_data.get("IoU", 0.0),
            cycle_id=objects_data.get("cycle_id", 0),
            is_paused=payload.get("is_paused", False),
            connected_players=payload.get("connected_players", 0),
            total_players=payload.get("total_players", 0),
            reset=payload.get("reset", False),
        )
