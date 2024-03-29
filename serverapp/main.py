import os
import sys
import enum
import django
import pathlib
import logging
import socketserver
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError


sys.path.append(pathlib.Path(__file__).resolve().parent)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverdb.settings')
django.setup()


from common.exceptions import ServerAppException
from serverapp.handler import ServerHandler


class ServerApp:

    PORT_FILENAME = 'port.info'

    logger = logging.getLogger(__name__)

    class States(enum.Enum):
        OFFLINE, ONLINE = range(2)

    clients = []
    messages = []

    def _init_db(self) -> None:
        self.logger.debug("migrate")
        with StringIO() as out:
            call_command("makemigrations", "serverapp", stdout=out)
            self.logger.debug(out.getvalue())
            call_command("migrate", stdout=out)
            self.logger.debug(out.getvalue())
            call_command("sqlmigrate", "serverapp", "0001", stdout=out)

    def _create_superuser(self) -> None:
        import os
        os.environ.setdefault('DJANGO_SUPERUSER_USERNAME', 'admin')
        os.environ.setdefault('DJANGO_SUPERUSER_PASSWORD', 'admin')
        os.environ.setdefault('DJANGO_SUPERUSER_EMAIL', 'random@gmail.com')
        with StringIO() as out:
            try:
                call_command("createsuperuser", "--noinput", stdout=out)
            except CommandError:
                pass  # user already exists

    def _run_django_server(self) -> None:
        import os
        os.system("python manage.py runserver")

    def _start_django_server(self) -> None:
        import threading
        thread = threading.Thread(
            target=self._run_django_server,
            name="Run Django Server",
        )
        thread.start()

    def _read_port(self) -> int:
        with open(ServerApp.PORT_FILENAME) as file:
            try:
                content = file.read()
            except IOError as e:
                raise ServerAppException(
                    f"Could not read port file {ServerApp.PORT_FILENAME}: {e}")

        try:
            port = int(content.strip())
        except ValueError:
            raise ServerAppException(
                f"Invalid port format: {content}. Should be an integer.")
        return port

    def __init__(self):
        self._init_db()
        self._create_superuser()
        self._start_django_server()
        self.host = '127.0.0.1'  # TODO: socket.gethostname()?
        self.port = self._read_port()

    def run(self):
        self.logger.debug(f"Listening on {self.host}:{self.port}")
        with socketserver.ThreadingTCPServer(
                (self.host, self.port), ServerHandler) as server:
            server.serve_forever()


def run():
    server = ServerApp()
    server.run()
