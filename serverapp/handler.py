import logging
import socketserver
from typing import Dict, Tuple, Union, NewType, Type
from itertools import dropwhile

from django.core.exceptions import ValidationError, ObjectDoesNotExist

from common import exceptions
from common.handlerbase import HandlerBase
from common.utils import camel_case_to_snake_case, FieldsValues
from common.packer import Packer
from serverapp.models import Client, Message
from protocol.packets.request import Request, PushMessageRequest
from protocol.packets.response import Response


class ServerHandler(HandlerBase, socketserver.BaseRequestHandler):

    Clients = NewType('Clients', Tuple[Union[int, str], ...])
    Messages = NewType('Messages', Tuple[str, ...])

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
            return {'receiver_client_id': client.id}

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

    def _get_symmetric_key_request(self):
        pass

    def get_concrete_message_type(
            self, message_type: int,
    ) -> Type[PushMessageRequest]:
        for packet in Request.ALL_MESSAGES:
            if message_type == packet.MESSAGE_TYPE:
                return packet
        raise ValueError(f"Unexpected message type {message_type}!")

    def _pop_messages(
            self, fields: FieldsValues,
    ) -> Dict[str, Union[int, Messages]]:
        from serverapp.models import Message
        print("POP MESSAGES")
        print(fields.items())
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
                f"Invalid IDs {sender_client_id}, {receiver_client_id}: {e!r}."
            )
        content = fields['content']
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

    def handle(self) -> None:
        from protocol.packets.response import ErrorResponse
        # TODO: wrap with try and log errors
        try:
            request_type, fields, _ = self._expect_packet(self.request, Request())
            request_name = request_type.__class__.__name__[:-7]  # omit 'Request'
            method_name = '_' + camel_case_to_snake_case(request_name)
            response_kwargs = getattr(self, method_name)(fields)
            logging.info(f'result: {response_kwargs}')
            response_name = request_name + 'Response'

            response_type = next(dropwhile(
                lambda response_t: response_t.__name__ != response_name,
                Response.ALL_RESPONSES,
            ))
            logging.debug(f"response_kwargs: {response_kwargs}")
            response_bytes = Packer(response_type()).pack(**response_kwargs)
            self.request.send(response_bytes)
        except Exception as e:
            logging.exception(e)
            error_bytes = Packer(ErrorResponse()).pack()
            self.request.send(error_bytes)
        else:
            client_address = self.client_address[0]
            logging.info(f"Responded to {client_address} successfully.")
