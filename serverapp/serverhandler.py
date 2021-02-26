import re
import logging
import socketserver
from typing import Dict, Any

from django.core.exceptions import ValidationError

from protocol import exceptions
from protocol.handlerbase import HandlerBase
from serverapp.models import Client, Message
from protocol.request import Request
from protocol.response import *


class ServerHandler(HandlerBase, socketserver.BaseRequestHandler):

    def _recv(self, buffer_size: int) -> bytes:
        return self.request.recv(buffer_size)

    def _expect_request(self):
        return self._expect_packet(Request)

    """ Actions """

    def _register(self, payload_fields: Dict[str, Any]) -> Dict[str, int]:
        clients_count = Client.objects.count()
        if clients_count > 2 ** 128 - 1:
            raise exceptions.ClientValidationError()
        try:
            client = Client.objects.create(
                name=payload_fields['name'],
                public_key=payload_fields['public_key'],
            )
        except ValidationError as e:
            raise exceptions.ClientValidationError()
        else:
            return {'new_client_id': client.id}

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

    def camel_case_to_snake_case(self, text: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()

    def handle(self):
        request, header_fields, payload_fields = self._expect_request()
        request_name = request.__name__[:-7]  # omit 'Request'
        logging.debug(request_name)
        method_name = '_' + self.camel_case_to_snake_case(request_name)
        response_kwargs = getattr(self, method_name)(payload_fields)
        logging.info(f'result: {response_kwargs}')
        response_name = request_name + 'Response'
        response_bytes = globals()[response_name](**response_kwargs).pack()
        self.request.send(response_bytes)
