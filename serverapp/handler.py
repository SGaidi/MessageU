import logging
import socketserver
from typing import Dict, Any, Tuple, Union
from itertools import dropwhile

from django.core.exceptions import ValidationError

from common import exceptions
from common.handlerbase import HandlerBase
from common.utils import camel_case_to_snake_case, Fields
from serverapp.models import Client, Message
from protocol.packets.request import Request
from protocol.packets.response import Response


class ServerHandler(HandlerBase, socketserver.BaseRequestHandler):

    def _register(self, payload_fields: Fields) -> Dict[str, int]:
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
            return {'receiver_client_id': client.id}

    def _list_clients(self, payload_fields: Fields) -> Dict[str, Tuple[Union[int, str], ...]]:
        clients = Client.objects.all()
        clients_dicts = []
        for client in clients:
            clients_dicts.append(client.id)
            clients_dicts.append(client.name)
        return {'clients': tuple(clients_dicts), 'clients_count': len(clients)}

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
                self._expect_packet(self.request, Request())
            request_name = request_type.__class__.__name__[:-7]  # omit 'Request'
            method_name = '_' + camel_case_to_snake_case(request_name)
            response_kwargs = getattr(self, method_name)(payload_fields)
            logging.info(f'result: {response_kwargs}')
            response_name = request_name + 'Response'

            response_type = next(dropwhile(
                lambda response_t: response_t.__name__ != response_name,
                Response.ALL,
            ))
            logging.debug(f"response_kwargs: {response_kwargs}")
            response_bytes = response_type().pack(**response_kwargs)
            self.request.send(response_bytes)
            logging.debug(f"Sent {len(response_bytes)}")
        except Exception as e:
            logging.exception(e)
        else:
            logging.info(f"Responded to {self.client_address[0]} successfully.")
