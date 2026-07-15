from copy import deepcopy


GAME_CONFIG = {
    "screen": {
        "caption": "Projeto de TCC - Gabriel",
        "height": 900,
        "width": 1200,
    },
    "game": {
        "playerNum": 4,
        "playerTam": 10,
        "objectsNum": 2,
        "objectBaseSquareTam": 50,
        "transparency": 50,
    },
    "server": {
        "showMonitor": True,
        "ip": "allowing-modern-dragon.ngrok-free.app",
        "port": 8000,
    },
    "scenario": {
        "scenario": 1,
        "c_1": ["human", "human", "human"],
        "c_2": ["human", "LLM", "human"],
        "c_3": ["LLM", "human", "LLM"],
        "c_4": ["LLM", "LLM", "LLM"],
    },
}

COLOR_CONFIG = {
    "background": [255, 219, 187],
    "blue": [0, 0, 255],
    "pink": [255, 0, 155],
    "yellow": [255, 255, 0],
    "cyan": [0, 255, 255],
    "magenta": [255, 0, 255],
    "white": [255, 255, 255],
    "black": [0, 0, 0],
    "red": [255, 0, 0],
    "green": [0, 255, 0],
    "orange": [255, 165, 0],
    "purple": [128, 0, 128],
    "brown": [139, 69, 19],
    "gray": [128, 128, 128],
    "light_gray": [211, 211, 211],
    "dark_gray": [64, 64, 64],
    "navy": [0, 0, 128],
    "teal": [0, 128, 128],
    "lime": [50, 205, 50],
    "gold": [255, 215, 0],
    "beige": [245, 245, 220],
    "coral": [255, 127, 80],
    "turquoise": [64, 224, 208],
    "violet": [238, 130, 238],
    "indigo": [75, 0, 130],
}


class YamlConfig:
    """In-memory config holder (kept name for existing call sites)."""

    def __init__(self, data: dict):
        self.data = data


def load_game_configs() -> tuple[YamlConfig, YamlConfig]:
    return YamlConfig(deepcopy(GAME_CONFIG)), YamlConfig(deepcopy(COLOR_CONFIG))
