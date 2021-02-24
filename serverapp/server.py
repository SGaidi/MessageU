import enum
import socket
import logging
import threading
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError

from mysite import exceptions
from serverapp.connection import Connection


socket.setdefaulttimeout(30)
logging.getLogger().setLevel(logging.DEBUG)


class ServerApp:

    VERSION = 2
    PORT_FILENAME = 'port.info'
    MIN_PORT = 1024
    MAX_PORT = 65353
    SOCKET_BACKLOG = 3

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
            try:
                call_command("createsuperuser", "--noinput", stdout=out)
            except CommandError:
                pass  # user already exists

    @staticmethod
    def _run_django_server():
        import os
        os.system("python manage.py runserver")

    @staticmethod
    def _start_django_server():
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
        self.socket = socket.socket()

    def run(self):
        host = socket.gethostname()
        self.socket.bind((host, self.port))
        self.socket.listen(ServerApp.SOCKET_BACKLOG)

        while True:
            try:
                client_socket, address = self.socket.accept()
            except Exception as e:
                logging.exception(f"something happened: {e}")
            else:
                thread = threading.Thread(
                    target=Connection.handle,
                    name="Handle Client Connection",
                    args=(client_socket, address),
                )
                thread.start()
                logging.info(f"handled request successfully")

        self.socket.close()