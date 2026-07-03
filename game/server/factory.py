import datetime

from game.server.application import GameServer
from game.server.cycle import CycleGenerator
from game.server.logger import SessionLogger
from game.server.monitor import ServerMonitor
from game.shared.config import YamlConfig
from game.shared.config import load_game_configs
from game.shared.settings import GameSettings
from game.shared.shapes import SHAPE_CLASSES


def build_model_vertices(game_config: YamlConfig) -> dict[str, list]:
    return {key: cls(game_config).vertices for key, cls in SHAPE_CLASSES.items()}


def create_server(
    game_config: YamlConfig | None = None,
    color_config: YamlConfig | None = None,
) -> GameServer:
    if game_config is None or color_config is None:
        game_config, color_config = load_game_configs()

    settings = GameSettings.from_yaml(game_config.data, color_config.data)
    model_vertices = build_model_vertices(game_config)
    shape_options = list(SHAPE_CLASSES.keys())

    timestamp = datetime.datetime.now().strftime("%d_%m_%H_%M_%S")
    session_logger = SessionLogger(timestamp, settings.player_colors)
    session_logger.log_metadata(game_config.data)

    cycle_generator = CycleGenerator(settings, model_vertices, shape_options)

    monitor_factory = None
    if settings.show_monitor:
        screen_config = game_config.data
        color_palette = color_config.data

        def monitor_factory(
            screen_config=screen_config,
            color_palette=color_palette,
            model_vertices=model_vertices,
        ):
            return ServerMonitor(screen_config, color_palette, model_vertices)

    return GameServer(
        settings=settings,
        cycle_generator=cycle_generator,
        session_logger=session_logger,
        model_vertices=model_vertices,
        monitor_factory=monitor_factory,
    )
