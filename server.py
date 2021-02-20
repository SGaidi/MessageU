import enum
import logging

import exceptions


class Server:

    VERSION = 1
    PORT_FILENAME = 'port.info'
    MIN_PORT = 1024
    MAX_PORT = 65353

    class States(enum.Enum):
        OFFLINE, ONLINE = range(2)

    logger = logging.Logger("Server")
    clients = []
    messages = []

    @staticmethod
    def _read_port() -> int:
        with open(Server.PORT_FILENAME) as file:
            try:
                content = file.read()
            except IOError as e:
                raise exceptions.ServerEnvironmentException(
                    f"Could not read port file {Server.PORT_FILENAME}: {e}")
        try:
            port = int(content.strip())
        except ValueError as e:
            raise exceptions.ServerConfigurationError(
                f"Invalid port format: {content}. Should be an integer.")
        if not (Server.MIN_PORT <= port <= Server.MAX_PORT):
            raise exceptions.ServerConfigurationError(
                f"Invalid port ({port}), "
                f"not in range: ({Server.MIN_PORT}, {Server.MAX_PORT})"
            )
        return port

    def __init__(self):
        self.port = Server._read_port()

    def respond(self):
        # TODO: encrypt E2E
        # TODO: each request should be stateless
        # usage threading / selector (asyncio?)
        pass
