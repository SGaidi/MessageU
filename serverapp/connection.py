from django.core.exceptions import ValidationError

from mysite import exceptions
from serverapp.models import Client, Message


class Connection:

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
        # TODO: with lock?
        messages = Message.objects.filter(to_client=request.client)
        # TODO: convert data to other type
        Message.objects.all().delete()
        return messages

    def handle_request(self, client_socket, address):

        pass