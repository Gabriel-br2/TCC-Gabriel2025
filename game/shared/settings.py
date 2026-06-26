from dataclasses import dataclass


@dataclass(frozen=True)
class GameSettings:
    screen_width: int
    screen_height: int
    screen_caption: str
    num_players: int
    num_objects: int
    object_base_square_size: int
    transparency: int
    server_bind_host: str
    server_connect_host: str
    server_port: int
    show_monitor: bool
    player_colors: tuple[str, ...]

    @classmethod
    def from_yaml(cls, game_config: dict, color_config: dict) -> "GameSettings":
        player_colors = tuple(list(color_config.keys())[1:])
        return cls(
            screen_width=game_config["screen"]["width"],
            screen_height=game_config["screen"]["height"],
            screen_caption=game_config["screen"]["caption"],
            num_players=game_config["game"]["playerNum"],
            num_objects=game_config["game"]["objectsNum"],
            object_base_square_size=game_config["game"]["objectBaseSquareTam"],
            transparency=game_config["game"]["transparency"],
            server_bind_host="0.0.0.0",
            server_connect_host=game_config["server"]["ip"],
            server_port=game_config["server"]["port"],
            show_monitor=game_config["server"]["showMonitor"],
            player_colors=player_colors,
        )

    @property
    def screen_config(self) -> dict:
        return {
            "screen": {
                "width": self.screen_width,
                "height": self.screen_height,
                "caption": self.screen_caption,
            }
        }
