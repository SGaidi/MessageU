import os
import sys
import pathlib

import django


sys.path.append(pathlib.Path(__file__).resolve().parent)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverdb.settings')
django.setup()


from serverapp.server import ServerApp


def run():
    server = ServerApp()
    server.run()
