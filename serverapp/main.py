import os
import sys
import pathlib

import django


sys.path.append(pathlib.Path(__file__).resolve().parent)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()


from serverapp.models import ServerApp  # noqa


def run():
    server = ServerApp()
    server.run()
