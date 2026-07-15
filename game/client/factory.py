import argparse

from game.client.application import ClientApplication
from game.client.network import GameClient
from game.client.objects import ClientObjectFactory
from game.client.screen import Screen
from game.shared.config import load_game_configs
from game.shared.settings import GameSettings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--player",
        type=str,
        default="human",
        choices=["human", "LLM"],
        help="Choose the type of player",
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["api", "local"],
        help="LLM source (required if --player=LLM)",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Specify name of the agent (required if --player=LLM)",
    )
    parser.add_argument(
        "--memory",
        type=str,
        help="path for memory history for LLM agent (optional, default is None)",
    )
    args = parser.parse_args(argv)

    if args.player == "LLM":
        if not args.source:
            parser.error("The --source argument is required when --player is LLM.")
        if not args.name:
            parser.error("The --name argument is required when --player is LLM.")

    if args.player == "human":
        if args.source:
            parser.error("The --source argument is not valid when --player is human.")
        if args.memory:
            parser.error("The --memory argument is not valid when --player is human.")

    return args


def create_client_application(args: argparse.Namespace) -> ClientApplication:
    game_config, color_config = load_game_configs()
    settings = GameSettings.from_yaml(game_config.data, color_config.data)

    screen = Screen(
        game_config.data,
        color_config.data,
        args.player,
        args.name,
        args.memory,
    )
    network = GameClient(settings, args.player, screen.name_id)
    object_factory = ClientObjectFactory(
        settings,
        color_config.data,
        game_config,
        screen.screen,
    )
    return ClientApplication(screen, network, object_factory, settings)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    application = create_client_application(args)

    initial_data = application.connect_until_ready()
    if initial_data:
        application.start_session(initial_data, args.source)

    application.shutdown()
    print("Programa encerrado.")
