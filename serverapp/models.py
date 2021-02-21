import enum
import logging
from io import StringIO

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from enumchoicefield import EnumChoiceField, ChoiceEnum
from django.core.management import call_command
from django.core.exceptions import ValidationError

from mysite import exceptions


logging.getLogger().setLevel(logging.DEBUG)


class Client(models.Model):

    # TODO: override tables names

    id = models.PositiveIntegerField(
        primary_key=True, help_text="Unique identifier",
        validators=[MinValueValidator(0), MaxValueValidator(2**128 - 1)])
    # Python strings are UTF-8, because ASCII is a subset of UTF-8, it's valid
    name = models.CharField(
        max_length=255, help_text="Client's provided name", unique=True)
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

    @staticmethod
    def _init_db():
        logging.info("migrate")
        with StringIO() as out:
            call_command("makemigrations", "serverapp", stdout=out)
            logging.info(out.getvalue())
            call_command("migrate", stdout=out)
            logging.info(out.getvalue())
            call_command("sqlmigrate", "serverapp", "0001", stdout=out)

    @staticmethod
    def _create_superuser():
        import os
        os.environ.setdefault('DJANGO_SUPERUSER_USERNAME', 'admin')
        os.environ.setdefault('DJANGO_SUPERUSER_PASSWORD', 'admin')
        os.environ.setdefault('DJANGO_SUPERUSER_EMAIL',
                              'gaidi.sarah@gmail.com')
        with StringIO() as out:
            call_command("createsuperuser", "--noinput", stdout=out)

    @staticmethod
    def _run_django_server():
        import os
        os.system("python manage.py runserver")

    @staticmethod
    def _start_django_server():
        import threading
        thread = threading.Thread(
            target=ServerApp._run_django_server,
            name="Run Django Server",
        )
        thread.start()

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
        ServerApp._init_db()
        ServerApp._create_superuser()
        ServerApp._start_django_server()
        self.port = ServerApp._read_port()

    def _register_client(self, request):
        try:
            client = Client.objects.create()
        except ValidationError as e:
            raise exceptions.ClientValidationError()

    def _list_clients(self, request):
        return Client.objects.all()

    def _push_message(self, request):
        try:
            message = Message.objects.create()
        except ValidationError as e:
            raise exceptions.MessageValidationError()

    def _pull_messages(self, request):
        # TODO: with lock
        messages = Message.objects.filter(to_client=request.client)
        # TODO: convert data to other type
        Message.objects.all().delete()
        return messages

    def _respond(self, request):
        # TODO: encrypt E2E
        pass

    def run(self):
        # TODO: each request should be stateless
        # usage threading / selector (asyncio?)

        # open port, listen

        while True:
            try:
                request = "something"
                import time
                time.sleep(1)
                self._respond(request)
                logging.info("waiting")
            except Exception as e:
                logging.exception(f"something happened: {e}")
            else:
                logging.info(f"handled request successfully")
