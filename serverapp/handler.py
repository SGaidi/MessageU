import logging
import socketserver
from typing import Dict, Any
from itertools import dropwhile

from django.core.exceptions import ValidationError

from common import exceptions
from common.handlerbase import HandlerBase
from common.utils import camel_case_to_snake_case
from serverapp.models import Client, Message
from protocol.packets.response import Response


class ServerHandler(HandlerBase, socketserver.BaseRequestHandler):

    def _recv(self, buffer_size: int) -> bytes:
        return self.request.recv(buffer_size)

    """ Actions """

    def _register(self, payload_fields: Dict[str, Any]) -> Dict[str, int]:
        clients_count = Client.objects.count()
        if clients_count > 2 ** 128 - 1:
            raise exceptions.ClientValidationError()
        try:
            client = Client.objects.create(
                name=payload_fields['client_name'],
                public_key=payload_fields['public_key'],
            )
        except Exception as e:
            raise exceptions.ClientValidationError("User already exists!")
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

    def handle(self) -> None:
        # TODO: wrap with try and log errors
        try:
            request_type, header_fields, payload_fields = \
                self._expect_packet(self.request)
            request_name = request_type.__class__.__name__[:-7]  # omit 'Request'
            method_name = '_' + camel_case_to_snake_case(request_name)
            response_kwargs = getattr(self, method_name)(payload_fields)
            logging.info(f'result: {response_kwargs}')
            response_name = request_name + 'Response'

            response_type = next(dropwhile(
                lambda response_t: response_t.__name__ != response_name,
                Response.ALL,
            ))

            response_bytes = response_type().pack(**response_kwargs)
            self.request.send(response_bytes)
        except Exception as e:
            logging.exception(e)
