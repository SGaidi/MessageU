import logging
import socketserver
from typing import Dict, Tuple, Union, NewType, Type, Callable
from itertools import dropwhile

from django.core.exceptions import ValidationError, ObjectDoesNotExist

from common import exceptions
from common.handlerbase import HandlerBase
from common.utils import camel_case_to_snake_case, FieldsValues
from common.packer import Packer
from serverapp.models import Client, Message
from protocol.packets.base import PacketBase
from protocol.packets.request.base import Request
from protocol.packets.response.responses import ALL_RESPONSES


class ServerHandler(HandlerBase, socketserver.BaseRequestHandler):

    Clients = NewType('Clients', Tuple[Union[int, str], ...])
    Messages = NewType('Messages', Tuple[str, ...])

    logger = logging.getLogger(__name__)

    def _register(self, fields: FieldsValues) -> Dict[str, int]:
        clients_count = Client.objects.count()
        if clients_count > 2 ** 128 - 1:
            raise exceptions.ClientValidationError("Too many clients.")

        try:
            client = Client.objects.create(
                name=fields['client_name'],
                public_key=fields['public_key'],
            )
        except Exception as e:
            raise exceptions.ClientValidationError(
                f"Failed to create Client: {e!r}"
            )
        else:
            return {'new_client_id': client.id}

    def _list_clients(
            self, fields: FieldsValues,
    ) -> Dict[str, Union[int, Clients]]:
        clients = Client.objects.all()
        # we won't exclude the sender client, that's because the local me.info
        #  file might be compromised - it's better to get a clear image.
        clients_list = []
        for client in clients:
            clients_list.append(client.id)
            clients_list.append(client.name)
        return {'clients': tuple(clients_list), 'clients_count': len(clients)}

    def _public_key(self, fields: FieldsValues) -> Dict[str, str]:
        receiver_client_id = fields['requested_client_id']
        try:
            client = Client.objects.get(id=receiver_client_id)
        except ObjectDoesNotExist:
            raise ValueError(f"No client with the ID {receiver_client_id}.")
        else:
            return {
                'requested_client_id': client.id,
                'public_key': client.public_key,
            }

    def _pop_messages(
            self, fields: FieldsValues,
    ) -> Dict[str, Union[int, Messages]]:
        from serverapp.models import Message

        sender_client_id = fields['sender_client_id']
        messages = Message.objects.filter(to_client__id=sender_client_id)

        messages_tuples = []
        for message in messages:
            messages_tuples.extend([
                message.from_client.id,
                message.id,
                message.message_type,
                len(message.content),
                message.content,
            ])
        messages.delete()

        return {
            'messages': tuple(messages_tuples),
            'messages_count': len(messages_tuples) // 5,
        }

    def _push_message(self, fields: FieldsValues):
        sender_client_id = fields['sender_client_id']
        receiver_client_id = fields['receiver_client_id']
        try:
            sender_client = Client.objects.get(id=sender_client_id)
            receiver_client = Client.objects.get(id=receiver_client_id)
        except Exception as e:
            raise exceptions.MessageValidationError(
                f"Invalid IDs ({sender_client_id}, {receiver_client_id}): "
                f"{e!r}."
            )
        content = fields.get('content', b'')
        message_type = fields['message_type']

        try:
            message = Message.objects.create(
                message_type=message_type,
                from_client=sender_client,
                to_client=receiver_client,
                content=content,
            )
        except ValidationError as e:
            raise exceptions.MessageValidationError(e)

        return {'receiver_client_id': receiver_client_id,
                'message_id': message.id}

    def _request_type_to_method_and_response_type(
            self, request_type: PacketBase,
    ) -> Tuple[Callable, Type[Request]]:
        request_name = request_type.__class__.__name__[:-7]  # omit 'Request'
        response_name = request_name + 'Response'
        method_name = '_' + camel_case_to_snake_case(request_name)
        response_type = next(dropwhile(
            lambda response_t: response_t.__name__ != response_name,
            ALL_RESPONSES,
        ))
        return getattr(self, method_name), response_type

    def handle(self) -> None:
        from django.utils import timezone
        from protocol.packets.request.requests import RegisterRequest
        from protocol.packets.response.responses import ErrorResponse

        try:
            # expect a request
            request_type, fields = self._expect_packet(self.request, Request())
            self.logger.debug(f"{request_type.__class__.__name__}: {fields}")
            # determine action and response
            method, response_type = \
                self._request_type_to_method_and_response_type(request_type)
            # call corresponding method
            response_kwargs = method(fields)
            self.logger.debug(f'result: {response_kwargs}')
            # update last seen after valid request
            if request_type.__class__.__name__ != 'RegisterRequest':
                Client.objects.filter(
                    pk=fields['sender_client_id'],
                ).update(last_seen=timezone.now())
            # pack and send a response
            response_bytes = Packer(response_type()).pack(**response_kwargs)
            self.request.send(response_bytes)
            # log about success
            client_address = self.client_address[0]
            self.logger.debug(f"Responded to {client_address} successfully.")
        except Exception as e:
            self.logger.exception(e)
            # pack and send an error response
            error_bytes = Packer(ErrorResponse()).pack()
            self.request.send(error_bytes)
