import os
import sys
import argparse
import pathlib

import server
import client


sys.path.append(pathlib.Path(__file__).resolve().parent)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messageu.settings')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="messageu",
        description="Run a messageu Server or Client",
    )
    parser.add_argument(
        name="run", choices=["server", "client"],
    )
    args = parser.parse_args()

    if args.run == "server":
        s = server.Server()
        s.run()
    else:  # args.run == "client":
        c = client.Client()
        c.run()
