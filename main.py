import os
import sys
import argparse
import pathlib

import django


sys.path.append(pathlib.Path(__file__).resolve().parent)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()


from serverapp.models import ServerApp  # noqa
from clientapp.models import ClientApp  # noqa


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="messageu",
        description="Run a messageu server or client",
    )
    parser.add_argument(
        dest="run", choices=["server", "client"],
    )
    args = parser.parse_args()

    if args.run == "server":
        server = ServerApp()
        # server.run()
    else:  # args.run == "client":
        client = ClientApp()
        client.run()
