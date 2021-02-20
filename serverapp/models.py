import enum
import logging
from io import StringIO

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from enumchoicefield import EnumChoiceField, ChoiceEnum
from django.core.management import call_command

from mysite import exceptions


logging.getLogger().setLevel(logging.DEBUG)


class Client(models.Model):

    # TODO: override tables names

    id = models.PositiveIntegerField(
        primary_key=True, help_text="Unique identifier",
        validators=[MinValueValidator(0), MaxValueValidator(2**128 - 1)])
    # Python strings are UTF-8, because ASCII is a subset of UTF-8, it's valid
    name = models.CharField(max_length=255, help_text="Client's provided name")
    public_key = models.BinaryField(
        max_length=160,
        help_text="Client's provided public-key used in message sending")
    last_seen = models.DateTimeField(
        null=True, blank=True,
        help_text="The last date and time the serverapp received a request "
                  "from the client")


class Message(models.Model):

    class MessageType(ChoiceEnum):
        one = "1"

    id = models.PositiveIntegerField(
        primary_key=True, help_text="Unique identifier",
        validators=[MinValueValidator(0), MaxValueValidator(2 ** 32 - 1)])
    to_client: models.ForeignKey(
        Client, help_text="The message recipient", on_delete=models.CASCADE)
    from_client: models.ForeignKey(
        Client, help_text="The message sender", on_delete=models.CASCADE)
    # did not use `type` name because it's a Python built-in
    message_type = EnumChoiceField(MessageType)  # TOOD:
    content = models.TextField(help_text="The message content")


class ServerApp:

    VERSION = 2
    PORT_FILENAME = 'port.info'
    MIN_PORT = 1024
    MAX_PORT = 65353

    class States(enum.Enum):
        OFFLINE, ONLINE = range(2)

    clients = []
    messages = []

    @classmethod
    def _init_db(cls):
        logging.info("migrate")
        with StringIO() as out:
            call_command("migrate", stdout=out)
            # TODO: flip the order of migrations?
            logging.info(out.getvalue())
            call_command("makemigrations", "serverapp", stdout=out)
            logging.info(out.getvalue())
            call_command("sqlmigrate", "serverapp", "0001", stdout=out)
            logging.info(out.getvalue())

    @staticmethod
    def _read_port() -> int:
        # TODO: add BASE_URL
        with open(ServerApp.PORT_FILENAME) as file:
            try:
                content = file.read()
            except IOError as e:
                raise exceptions.ServerAppEnvironmentException(
                    f"Could not read port file {ServerApp.PORT_FILENAME}: {e}")
        try:
            port = int(content.strip())
        except ValueError as e:
            raise exceptions.ServerAppConfigurationError(
                f"Invalid port format: {content}. Should be an integer.")
        if not (ServerApp.MIN_PORT <= port <= ServerApp.MAX_PORT):
            raise exceptions.ServerAppConfigurationError(
                f"Invalid port ({port}), "
                f"not in range: ({ServerApp.MIN_PORT}, {ServerApp.MAX_PORT})"
            )
        return port

    def __init__(self):
        logging.warning("HELLO")
        self._init_db()
        self.port = ServerApp._read_port()

    def respond(self):
        # TODO: encrypt E2E
        pass

    def run(self):
        # TODO: each request should be stateless
        # usage threading / selector (asyncio?)

        # open port, listen

        while True:
            try:
                #request = ...
                import time
                time.sleep(1)
                logging.info("waiting")
            except Exception as e:
                self.logger.exception(f"something happened: {e}")
            else:
                self.logger.info(f"handled request successfully")
