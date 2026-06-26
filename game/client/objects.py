from game.shared.config import YamlConfig
from game.shared.protocol import NON_PLAYER_KEYS
from game.shared.protocol import player_key
from game.shared.settings import GameSettings
from game.shared.shapes import SHAPE_CLASSES


class ClientObjectFactory:
    def __init__(
        self,
        settings: GameSettings,
        color_palette: dict,
        game_config: YamlConfig,
        pygame_surface,
    ):
        self._settings = settings
        self._colors = color_palette
        self._game_config = game_config
        self._surface = pygame_surface

    def from_server_payload(self, objects_data: dict, client_id: int) -> list:
        shapes = []
        for player, value in objects_data.items():
            if player in NON_PLAYER_KEYS:
                continue

            transparency = (
                255 if player == player_key(client_id) else self._settings.transparency
            )
            player_color = [*self._colors[value["color"]], transparency]

            for count, obj in enumerate(value["pos"]):
                shapes.append(
                    SHAPE_CLASSES[obj[-1]](
                        self._game_config,
                        int(player[1:]),
                        count,
                        self._surface,
                        player_color,
                        obj[:-1],
                    )
                )
        return sorted(
            shapes, key=lambda shape: (shape.id != client_id, shape.id, shape.obj_id)
        )
