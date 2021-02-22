from abc import ABC
from typing import Tuple

from protocol.base import Base


class Response(Base, ABC):

    VERSION = 2
    VERSION_LENGTH = 1
    CODE_LENGTH = 2
    MESSAGE_ID_LENGTH = 4

    def __str__(self):
        """Used for debug logging."""
        return "{}(code={}, length={})".format(
            self.__class__.__name__,
            self.code,
            len(self.payload),
        )


class RegisterSuccessfulResponse(Response):

    CODE = 1000

    def __init__(self, client_id: int):
        client_id_bytes = self.int_to_bytes(
            param=client_id, length=self.CLIENT_ID_LENGTH)
        super(RegisterSuccessfulResponse, self).__init__(
            payload=client_id_bytes)


class ListClientsResponse(Response):

    CODE = 1001

    def __init__(self, clients: Tuple[Tuple[int, str]]):
        clients_bytes = b''
        for client_id, client_name in clients:
            client_id_bytes = self.int_to_bytes(
                param=client_id, length=self.CLIENT_ID_LENGTH)
            client_name_bytes = self.int_to_bytes(
                param=client_name, length=self.NAME_LENGTH)
            clients_bytes += client_id_bytes + client_name_bytes
        super(ListClientsResponse, self).__init__(payload=clients_bytes)


class PublicKeyResponse(Response):

    CODE = 1002

    def __init__(self, client_id: int, public_key: bytes):
        client_id_bytes = self.int_to_bytes(
            param=client_id, length=self.CLIENT_ID_LENGTH)
        payload = client_id_bytes + public_key
        super(PublicKeyResponse, self).__init__(payload=payload)


class PushMessageResponse(Response):

    CODE = 1003

    def __init__(self, receiver_client_id: int, message_id: int):
        receiver_client_id_bytes = self.int_to_bytes(
            param=receiver_client_id, length=self.CLIENT_ID_LENGTH)
        message_id_bytes = self.int_to_bytes(
            param=message_id, length=self.MESSAGE_ID_LENGTH,
        )
        payload = receiver_client_id_bytes + message_id_bytes
        super(PushMessageResponse, self).__init__(payload=payload)


class PopMessagesResponse(Response):

    CODE = 1004

    def __init__(self, messages: Tuple[Tuple[int, int, int, bytes]]):
        messages_bytes = b''
        for client_id, message_id, message_type, content in messages:
            client_id_bytes = self.int_to_bytes(
                param=client_id, length=self.CLIENT_ID_LENGTH)
            message_id_bytes = self.int_to_bytes(
                param=message_id, length=self.MESSAGE_ID_LENGTH)
            message_type_bytes = self.int_to_bytes(
                param=message_type, length=self.MESSAGE_TYPE_LENGTH)
            message_bytes = client_id_bytes + message_id_bytes + \
                message_type_bytes
            messages_bytes += message_bytes
        super(PopMessagesResponse, self).__init__(payload=messages_bytes)
