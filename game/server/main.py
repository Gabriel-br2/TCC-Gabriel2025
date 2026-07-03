import asyncio
import logging

from game.server.factory import create_server


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    server = create_server()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logging.info("Server shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
