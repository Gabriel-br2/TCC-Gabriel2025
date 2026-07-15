NON_PLAYER_KEYS = frozenset({"IoU", "cycle_id"})
OBJECTIVE_THRESHOLD = 0.95
CALC_INTERVAL_SEC = 0.05 
SEND_EVERY_N_FRAMES = 1


def player_key(player_id: int) -> str:
    return f"P{player_id}"
